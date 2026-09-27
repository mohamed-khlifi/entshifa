"""Create and version clinic-owned document templates."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.engines.documents.placeholders import validate_placeholders
from ent.features.clinics.repository import ClinicRepository
from ent.features.documents.html_render import render_document_html
from ent.features.documents.letterhead import (
    compose_letterhead,
    sample_placeholder_data,
)
from ent.features.documents.models import DocumentTemplate, DocumentTemplateVersion
from ent.features.documents.repository import (
    DocumentTemplateRepository,
    DocumentTemplateVersionRepository,
)
from ent.features.documents.schemas.requests import (
    DocumentTemplateCreate,
    DocumentTemplatePreview,
    DocumentTemplateVersionCreate,
    placeholder_map,
)
from ent.features.documents.schemas.responses import (
    DocumentPreviewRead,
    DocumentTemplateDetailRead,
    DocumentTemplateRead,
)
from ent.features.documents.support import (
    assert_direction,
    page,
    placeholder_dict,
    raise_placeholder,
    require_placeholder_keys,
    template_detail,
    template_read,
    utcnow,
)


class DocumentTemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_templates(
        self,
        *,
        user: CurrentUser,
        page_params: PaginationParams | None,
    ) -> PageSchema[DocumentTemplateRead]:
        repo = DocumentTemplateRepository(self._session, clinic_id=user.clinic_id)
        result = await repo.list_active(page=page_params)
        AuditRecorder(self._session).record_access(
            action="list",
            entity_type="document_template",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return page(
            [template_read(row) for row in result.items],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    async def create_template(
        self,
        *,
        user: CurrentUser,
        body: DocumentTemplateCreate,
    ) -> DocumentTemplateRead:
        placeholders = placeholder_dict(body)
        require_placeholder_keys(placeholders)
        repo = DocumentTemplateRepository(self._session, clinic_id=user.clinic_id)
        existing = await repo.get_by_code(body.code)
        if existing is not None and existing.clinic_id == user.clinic_id:
            raise ValidationError(reason="code", code=body.code)
        row = DocumentTemplate(
            clinic_id=user.clinic_id,
            code=body.code,
            category=body.category,
            placeholders=placeholders,
            is_system=False,
            is_active=True,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await repo.add(row)
        await self._session.commit()
        return template_read(row)

    async def add_template_version(
        self,
        *,
        user: CurrentUser,
        template_public_id: str,
        body: DocumentTemplateVersionCreate,
    ) -> DocumentTemplateRead:
        templates = DocumentTemplateRepository(self._session, clinic_id=user.clinic_id)
        template = await templates.get_by_public_id(template_public_id)
        if template is None or template.clinic_id != user.clinic_id:
            raise NotFoundError()
        assert_direction(body.locale, body.direction)
        placeholders = placeholder_map(dict(template.placeholders))
        declared = set(placeholders)
        issue = validate_placeholders(
            (body.header_html, body.body_html, body.footer_html),
            declared,
        )
        if issue is not None:
            raise_placeholder(issue)
        versions = DocumentTemplateVersionRepository(
            self._session, clinic_id=user.clinic_id
        )
        revision = await versions.next_version(
            template_id=int(template.id),
            locale=body.locale,
        )
        versions.session.add(
            DocumentTemplateVersion(
                clinic_id=user.clinic_id,
                document_template_id=int(template.id),
                version=revision,
                locale=body.locale,
                direction=body.direction,
                header_html=body.header_html,
                body_html=body.body_html,
                footer_html=body.footer_html,
                css=body.css,
                page_setup=body.page_setup.model_dump(),
                published_at=utcnow(),
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
        await self._session.commit()
        return template_read(template)

    async def get_template(
        self,
        *,
        user: CurrentUser,
        template_public_id: str,
    ) -> DocumentTemplateDetailRead:
        templates = DocumentTemplateRepository(self._session, clinic_id=user.clinic_id)
        template = await templates.get_by_public_id(template_public_id)
        if template is None:
            raise NotFoundError()
        versions = await DocumentTemplateVersionRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_template(int(template.id))
        AuditRecorder(self._session).record_access(
            action="read",
            entity_type="document_template",
            clinic_id=user.clinic_id,
            entity_id=int(template.id),
            entity_public_id=template.public_id,
        )
        await self._session.commit()
        return template_detail(template, versions)

    async def preview(
        self,
        *,
        user: CurrentUser,
        body: DocumentTemplatePreview,
    ) -> DocumentPreviewRead:
        assert_direction(body.locale, body.direction)
        placeholders = {
            key: {"type": spec.type, "required": spec.required}
            for key, spec in body.placeholders.items()
        }
        require_placeholder_keys(placeholders)
        declared = set(placeholders)
        issue = validate_placeholders(
            (body.header_html, body.body_html, body.footer_html),
            declared,
        )
        if issue is not None:
            raise_placeholder(issue)
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError()
        header, footer = await compose_letterhead(
            self._session,
            clinic_id=user.clinic_id,
            clinic=clinic,
            header_html=body.header_html,
            footer_html=body.footer_html,
        )
        issue = validate_placeholders((header, body.body_html, footer), declared)
        if issue is not None:
            raise_placeholder(issue)
        html = render_document_html(
            locale=body.locale,
            direction=body.direction,
            header_html=header,
            body_html=body.body_html,
            footer_html=footer,
            css=body.css,
            data=sample_placeholder_data(placeholders),
            page_setup=body.page_setup.model_dump(),
        )
        return DocumentPreviewRead(html=html)
