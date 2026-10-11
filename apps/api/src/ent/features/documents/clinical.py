"""Create a visit document and print a mixed-language batch."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.security.principal import CurrentUser
from ent.features.clinics.repository import ClinicRepository
from ent.features.documents.assemble import (
    build_document_data,
    is_clinical_template,
    resolve_document_locale,
)
from ent.features.documents.constants import DOCUMENT_LOCALES, IMAGING_REQUEST_CODE
from ent.features.documents.context import load_visit_facts
from ent.features.documents.exceptions import DocumentEncounterRequiredError
from ent.features.documents.html_render import (
    compose_visit_batch,
    render_document_sheet,
    render_sheet_from_snapshot,
)
from ent.features.documents.letterhead import compose_letterhead
from ent.features.documents.models import Document
from ent.features.documents.repository import (
    DocumentRepository,
    DocumentTemplateRepository,
    DocumentTemplateVersionRepository,
)
from ent.features.documents.schemas.requests import (
    DocumentBatchPreviewRequest,
    DocumentCreate,
    placeholder_map,
)
from ent.features.documents.schemas.responses import DocumentPreviewRead, DocumentRead
from ent.features.documents.support import (
    document_read,
    document_title,
    require_data,
)
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.settings import Settings, get_settings


async def create_clinical_document(
    session: AsyncSession,
    *,
    user: CurrentUser,
    body: DocumentCreate,
) -> DocumentRead:
    if not is_clinical_template(body.template_code):
        raise ValidationError(reason="template")
    if body.encounter_public_id is None:
        raise DocumentEncounterRequiredError()
    patient = await _patient(session, user, body.patient_public_id)
    clinic = await _clinic(session, user)
    encounter = await EncounterRepository(session, clinic_id=user.clinic_id).get_detail(
        body.encounter_public_id
    )
    if encounter is None or int(encounter.patient_id) != int(patient.id):
        raise NotFoundError()
    locale = resolve_document_locale(
        template_code=body.template_code,
        requested=body.locale,
        referring_doctor_locale=patient.referring_doctor_locale,
        preferred_locale=patient.preferred_locale,
        clinic_default_locale=clinic.default_locale,
    )
    if locale not in DOCUMENT_LOCALES:
        raise ValidationError(reason="locale", locale=locale)
    template = await DocumentTemplateRepository(
        session, clinic_id=user.clinic_id
    ).get_by_code(body.template_code)
    if template is None:
        raise NotFoundError()
    version = await DocumentTemplateVersionRepository(
        session, clinic_id=user.clinic_id
    ).latest(template_id=int(template.id), locale=locale)
    if version is None:
        raise NotFoundError()
    facts = await load_visit_facts(
        session,
        user,
        patient=patient,
        clinic=clinic,
        encounter=encounter,
        locale=locale,
    )
    data = build_document_data(
        facts,
        body,
        clinician_public_id=user.user_public_id,
    )
    require_data(placeholder_map(dict(template.placeholders)), data)
    row = Document(
        clinic_id=user.clinic_id,
        patient_id=int(patient.id),
        encounter_id=int(encounter.id),
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
    await DocumentRepository(session, clinic_id=user.clinic_id).add(row)
    AuditRecorder(session).record_access(
        action="create",
        entity_type="document",
        clinic_id=user.clinic_id,
        entity_id=int(row.id),
        entity_public_id=row.public_id,
        patient_id=int(patient.id),
    )
    await session.commit()
    return document_read(
        row,
        patient.public_id,
        template.code,
        encounter.public_id,
    )


async def preview_visit_batch(
    session: AsyncSession,
    *,
    user: CurrentUser,
    encounter_public_id: str,
    body: DocumentBatchPreviewRequest,
    settings: Settings | None = None,
) -> DocumentPreviewRead:
    resolved = settings or get_settings()
    encounter = await EncounterRepository(session, clinic_id=user.clinic_id).get_detail(
        encounter_public_id
    )
    if encounter is None:
        raise NotFoundError()
    await _patient_by_id(session, user, int(encounter.patient_id))
    clinic = await _clinic(session, user)
    rows = await DocumentRepository(
        session, clinic_id=user.clinic_id
    ).list_active_for_encounter(int(encounter.id))
    by_public_id = {row.public_id: row for row in rows}
    ordered: list[Document] = []
    for public_id in body.document_public_ids:
        found = by_public_id.get(public_id)
        if found is None:
            raise NotFoundError()
        ordered.append(found)
    sheets: list[str] = []
    for row in ordered:
        sheets.append(
            await _sheet(
                session,
                user=user,
                clinic=clinic,
                row=row,
                settings=resolved,
            )
        )
    AuditRecorder(session).record_access(
        action="read",
        entity_type="document",
        clinic_id=user.clinic_id,
        entity_public_id=encounter.public_id,
        patient_id=int(encounter.patient_id),
    )
    await session.commit()
    return DocumentPreviewRead(html=compose_visit_batch(sheets))


async def _sheet(
    session: AsyncSession,
    *,
    user: CurrentUser,
    clinic: Any,
    row: Document,
    settings: Settings,
) -> str:
    snapshot = row.content_snapshot if isinstance(row.content_snapshot, dict) else {}
    frozen = snapshot.get("template")
    if row.status == "final" and isinstance(frozen, dict):
        return render_sheet_from_snapshot(snapshot)
    template = await DocumentTemplateRepository(session, clinic_id=user.clinic_id).get(
        int(row.template_id)
    )
    version = await DocumentTemplateVersionRepository(
        session, clinic_id=user.clinic_id
    ).get_for_template(
        template_id=int(row.template_id),
        version_id=int(row.template_version_id),
    )
    if template is None or version is None:
        raise NotFoundError()
    header, footer = await compose_letterhead(
        session,
        clinic_id=user.clinic_id,
        clinic=clinic,
        header_html=version.header_html,
        footer_html=version.footer_html,
        settings=settings,
    )
    data = snapshot.get("data")
    if not isinstance(data, dict):
        raise ValidationError(reason="snapshot")
    page_setup = version.page_setup if isinstance(version.page_setup, dict) else {}
    return render_document_sheet(
        locale=version.locale,
        direction=version.direction,
        header_html=header,
        body_html=row.body_override_html or version.body_html,
        footer_html=footer,
        css=version.css,
        data=data,
        page_setup=dict(page_setup),
    )


async def _patient(session: AsyncSession, user: CurrentUser, public_id: str) -> Any:
    patient = await PatientRepository(session, clinic_id=user.clinic_id).get_visible(
        public_id, created_by_id=created_by_scope(user)
    )
    if patient is None:
        raise NotFoundError()
    return patient


async def _patient_by_id(
    session: AsyncSession, user: CurrentUser, patient_id: int
) -> Any:
    patient = await PatientRepository(session, clinic_id=user.clinic_id).get(patient_id)
    if patient is None:
        raise NotFoundError()
    scope = created_by_scope(user)
    if scope is not None and patient.created_by_id != scope:
        raise NotFoundError()
    return patient


async def _clinic(session: AsyncSession, user: CurrentUser) -> Any:
    clinic = await ClinicRepository(session).get(user.clinic_id)
    if clinic is None:
        raise NotFoundError()
    return clinic


def imaging_needs_recheck(template_code: str) -> bool:
    return template_code == IMAGING_REQUEST_CODE
