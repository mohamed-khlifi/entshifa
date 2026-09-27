"""Document draft, finalization, and download use cases (P1-09)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.errors.exceptions import (
    DocumentImmutableError,
    DocumentNotRenderedError,
    NotFoundError,
    ValidationError,
)
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.engines.documents.content_hash import content_hash
from ent.engines.documents.placeholders import validate_placeholders
from ent.features.attachments.repository import AttachmentRepository
from ent.features.clinics.repository import ClinicRepository
from ent.features.documents.chart import load_summary_data
from ent.features.documents.constants import DOCUMENT_LOCALES
from ent.features.documents.html_render import (
    render_document_html,
    render_from_snapshot,
)
from ent.features.documents.letterhead import compose_letterhead
from ent.features.documents.models import (
    Document,
    DocumentRecipient,
    DocumentTemplate,
    DocumentTemplateVersion,
)
from ent.features.documents.repository import (
    DocumentRecipientRepository,
    DocumentRepository,
    DocumentTemplateRepository,
    DocumentTemplateVersionRepository,
)
from ent.features.documents.schemas.requests import (
    DocumentCreate,
    DocumentFinalize,
    DocumentRecipientCreate,
    placeholder_map,
)
from ent.features.documents.schemas.responses import (
    DocumentDownloadRead,
    DocumentPreviewRead,
    DocumentRead,
    DocumentRecipientRead,
)
from ent.features.documents.support import (
    document_read,
    document_title,
    page,
    raise_placeholder,
    require_data,
    utcnow,
)
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.integrations.storage import get_object_storage
from ent.jobs.queue import enqueue_job
from ent.jobs.tasks.render_document import JOB_RENDER_DOCUMENT
from ent.settings import Settings, get_settings


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()

    async def create_document(
        self,
        *,
        user: CurrentUser,
        body: DocumentCreate,
    ) -> DocumentRead:
        patient = await self._patient(user, body.patient_public_id)
        clinic = await self._clinic(user)
        template, version = await self._template_version(
            user,
            code=body.template_code,
            locale=body.locale or patient.preferred_locale,
        )
        data = await load_summary_data(
            self._session,
            user,
            patient=patient,
            clinic=clinic,
            locale=version.locale,
        )
        require_data(placeholder_map(dict(template.placeholders)), data)
        row = Document(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            template_id=int(template.id),
            template_version_id=int(version.id),
            category=template.category,
            locale=version.locale,
            title=document_title(version),
            status="draft",
            content_snapshot={"data": data},
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await DocumentRepository(self._session, clinic_id=user.clinic_id).add(row)
        await self._session.commit()
        return document_read(row, patient.public_id, template.code)

    async def list_documents(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page_params: PaginationParams | None,
    ) -> PageSchema[DocumentRead]:
        patient = await self._patient(user, patient_public_id)
        result = await DocumentRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient_id=int(patient.id), page=page_params)
        codes = await self._template_codes(
            user, {int(row.template_id) for row in result.items}
        )
        self._access(
            user,
            action="list",
            entity_type="document",
            patient_id=int(patient.id),
        )
        await self._session.commit()
        return page(
            [
                document_read(
                    row, patient.public_id, codes.get(int(row.template_id), "")
                )
                for row in result.items
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    async def get_document(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> DocumentRead:
        row = await self._document(user, public_id)
        patient = await self._patient_by_id(user, int(row.patient_id))
        code = await self._template_code(user, int(row.template_id))
        self._access(
            user,
            action="read",
            entity_type="document",
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        return document_read(row, patient.public_id, code)

    async def finalize_document(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: DocumentFinalize,
    ) -> DocumentRead:
        row = await self._document(user, public_id)
        if row.status != "draft":
            raise DocumentImmutableError()
        patient = await self._patient_by_id(user, int(row.patient_id))
        clinic = await self._clinic(user)
        template = await self._visible_template(user, int(row.template_id))
        version = await DocumentTemplateVersionRepository(
            self._session, clinic_id=user.clinic_id
        ).get_for_template(
            template_id=int(template.id),
            version_id=int(row.template_version_id),
        )
        if version is None:
            raise NotFoundError()
        chosen_body = body.body_override_html or version.body_html
        header, footer = await compose_letterhead(
            self._session,
            clinic_id=user.clinic_id,
            clinic=clinic,
            header_html=version.header_html,
            footer_html=version.footer_html,
            settings=self._settings,
        )
        placeholders = placeholder_map(dict(template.placeholders))
        issue = validate_placeholders(
            (header, chosen_body, footer),
            set(placeholders),
        )
        if issue is not None:
            raise_placeholder(issue)
        data = await load_summary_data(
            self._session,
            user,
            patient=patient,
            clinic=clinic,
            locale=version.locale,
        )
        require_data(placeholders, data)
        snapshot: dict[str, Any] = {
            "data": data,
            "template": {
                "code": template.code,
                "locale": version.locale,
                "direction": version.direction,
                "header_html": header,
                "body_html": chosen_body,
                "footer_html": footer,
                "css": version.css,
                "page_setup": dict(version.page_setup),
            },
        }
        row.content_snapshot = snapshot
        row.body_override_html = body.body_override_html
        row.content_hash = content_hash(snapshot)
        row.status = "final"
        row.finalized_at = utcnow()
        row.finalized_by_id = user.user_id
        row.updated_by_id = user.user_id
        row.title = document_title(version)
        await self._session.commit()
        await enqueue_job(
            job_name=JOB_RENDER_DOCUMENT,
            idempotency_key=f"render-document:{row.public_id}",
            payload={"document_public_id": row.public_id},
        )
        return document_read(row, patient.public_id, template.code)

    async def preview_html(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> DocumentPreviewRead:
        row = await self._document(user, public_id)
        await self._patient_by_id(user, int(row.patient_id))
        snapshot = (
            row.content_snapshot if isinstance(row.content_snapshot, dict) else {}
        )
        frozen = snapshot.get("template")
        if row.status == "final" and isinstance(frozen, dict):
            self._access(
                user,
                action="read",
                entity_type="document",
                entity_id=int(row.id),
                entity_public_id=row.public_id,
                patient_id=int(row.patient_id),
            )
            await self._session.commit()
            return DocumentPreviewRead(html=render_from_snapshot(snapshot))
        clinic = await self._clinic(user)
        template = await self._visible_template(user, int(row.template_id))
        version = await DocumentTemplateVersionRepository(
            self._session, clinic_id=user.clinic_id
        ).get_for_template(
            template_id=int(template.id),
            version_id=int(row.template_version_id),
        )
        if version is None:
            raise NotFoundError()
        header, footer = await compose_letterhead(
            self._session,
            clinic_id=user.clinic_id,
            clinic=clinic,
            header_html=version.header_html,
            footer_html=version.footer_html,
            settings=self._settings,
        )
        data = snapshot.get("data")
        if not isinstance(data, dict):
            patient = await self._patient_by_id(user, int(row.patient_id))
            data = await load_summary_data(
                self._session,
                user,
                patient=patient,
                clinic=clinic,
                locale=version.locale,
            )
        page_setup = version.page_setup if isinstance(version.page_setup, dict) else {}
        html = render_document_html(
            locale=version.locale,
            direction=version.direction,
            header_html=header,
            body_html=row.body_override_html or version.body_html,
            footer_html=footer,
            css=version.css,
            data=data,
            page_setup=dict(page_setup),
        )
        self._access(
            user,
            action="read",
            entity_type="document",
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        return DocumentPreviewRead(html=html)

    async def download_url(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> DocumentDownloadRead:
        row = await self._document(user, public_id)
        if row.rendered_attachment_id is None:
            raise DocumentNotRenderedError()
        attachment = await AttachmentRepository(
            self._session, clinic_id=user.clinic_id
        ).get(int(row.rendered_attachment_id))
        if attachment is None:
            raise NotFoundError()
        storage = get_object_storage(self._settings)
        ttl = self._settings.attachment_download_url_ttl_seconds
        presigned = await storage.create_presigned_download(
            key=attachment.storage_key,
            expires_in_seconds=ttl,
            filename=attachment.filename,
        )
        self._access(
            user,
            action="download",
            entity_type="document",
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        return DocumentDownloadRead(url=presigned.url, expires_in_seconds=ttl)

    async def add_recipient(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: DocumentRecipientCreate,
    ) -> DocumentRecipientRead:
        row = await self._document(user, public_id)
        if row.status == "cancelled":
            raise DocumentImmutableError()
        recipient = DocumentRecipient(
            clinic_id=user.clinic_id,
            document_id=int(row.id),
            recipient_type=body.recipient_type,
            name=body.name,
            channel=body.channel,
            address=body.address,
            locale=body.locale,
            delivery_status="pending",
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await DocumentRecipientRepository(self._session, clinic_id=user.clinic_id).add(
            recipient
        )
        await self._session.commit()
        return DocumentRecipientRead(
            public_id=recipient.public_id,
            recipient_type=recipient.recipient_type,
            name=recipient.name,
            channel=recipient.channel,
            locale=recipient.locale,
            delivery_status=recipient.delivery_status,
        )

    async def _template_version(
        self,
        user: CurrentUser,
        *,
        code: str,
        locale: str,
    ) -> tuple[DocumentTemplate, DocumentTemplateVersion]:
        if locale not in DOCUMENT_LOCALES:
            raise ValidationError(reason="locale", locale=locale)
        template = await DocumentTemplateRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_code(code)
        if template is None:
            raise NotFoundError()
        version = await DocumentTemplateVersionRepository(
            self._session, clinic_id=user.clinic_id
        ).latest(template_id=int(template.id), locale=locale)
        if version is None:
            raise NotFoundError()
        return template, version

    async def _visible_template(
        self, user: CurrentUser, template_id: int
    ) -> DocumentTemplate:
        template = await DocumentTemplateRepository(
            self._session, clinic_id=user.clinic_id
        ).get(template_id)
        if template is None:
            raise NotFoundError()
        return template

    async def _patient(self, user: CurrentUser, public_id: str) -> Any:
        patient = await PatientRepository(
            self._session, clinic_id=user.clinic_id
        ).get_visible(public_id, created_by_id=created_by_scope(user))
        if patient is None:
            raise NotFoundError()
        return patient

    async def _patient_by_id(self, user: CurrentUser, patient_id: int) -> Any:
        patient = await PatientRepository(self._session, clinic_id=user.clinic_id).get(
            patient_id
        )
        if patient is None:
            raise NotFoundError()
        scope = created_by_scope(user)
        if scope is not None and patient.created_by_id != scope:
            raise NotFoundError()
        return patient

    async def _clinic(self, user: CurrentUser) -> Any:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError()
        return clinic

    async def _document(self, user: CurrentUser, public_id: str) -> Document:
        row = await DocumentRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None:
            raise NotFoundError()
        return row

    async def _template_code(self, user: CurrentUser, template_id: int) -> str:
        codes = await self._template_codes(user, {template_id})
        return codes.get(template_id, "")

    async def _template_codes(
        self, user: CurrentUser, template_ids: set[int]
    ) -> dict[int, str]:
        repo = DocumentTemplateRepository(self._session, clinic_id=user.clinic_id)
        codes: dict[int, str] = {}
        for template_id in template_ids:
            template = await repo.get(template_id)
            if template is not None:
                codes[template_id] = template.code
        return codes

    def _access(
        self,
        user: CurrentUser,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        entity_public_id: str | None = None,
        patient_id: int | None = None,
    ) -> None:
        AuditRecorder(self._session).record_access(
            action=action,
            entity_type=entity_type,
            clinic_id=user.clinic_id,
            entity_id=entity_id,
            entity_public_id=entity_public_id,
            patient_id=patient_id,
        )
