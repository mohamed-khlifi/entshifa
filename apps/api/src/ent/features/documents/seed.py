"""Idempotent insert of the system patient-summary template."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.engines.documents.placeholders import validate_placeholders
from ent.features.documents.catalog import (
    PATIENT_SUMMARY_PLACEHOLDERS,
    declared_placeholder_names,
    patient_summary_versions,
    template_code,
)
from ent.features.documents.constants import PATIENT_SUMMARY_CODE
from ent.features.documents.models import DocumentTemplate, DocumentTemplateVersion
from ent.features.documents.repository import DocumentTemplateRepository


async def ensure_patient_summary_template(session: AsyncSession) -> None:
    """Insert the system template once. Later locale rows are added if missing."""

    repo = DocumentTemplateRepository(session, clinic_id=None)
    template = await repo.get_system_by_code(PATIENT_SUMMARY_CODE)
    if template is None:
        template = DocumentTemplate(
            clinic_id=None,
            code=template_code(),
            category="patient_summary",
            engine="html",
            placeholders=PATIENT_SUMMARY_PLACEHOLDERS,
            is_system=True,
            is_active=True,
        )
        session.add(template)
        await session.flush()

    for spec in patient_summary_versions():
        issue = validate_placeholders(
            (spec["header_html"], spec["body_html"], spec["footer_html"]),
            declared_placeholder_names(),
        )
        if issue is not None:
            msg = issue.reason
            raise RuntimeError(msg)
        existing = (
            await session.execute(
                select(DocumentTemplateVersion.id).where(
                    DocumentTemplateVersion.document_template_id == template.id,
                    DocumentTemplateVersion.locale == spec["locale"],
                    DocumentTemplateVersion.deleted_at.is_(None),
                )
            )
        ).first()
        if existing is not None:
            continue
        session.add(
            DocumentTemplateVersion(
                clinic_id=None,
                document_template_id=int(template.id),
                version=1,
                locale=str(spec["locale"]),
                direction=str(spec["direction"]),
                header_html=str(spec["header_html"]),
                body_html=str(spec["body_html"]),
                footer_html=str(spec["footer_html"]),
                css=str(spec["css"]),
                page_setup=dict(spec["page_setup"]),
                published_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )
    await session.flush()
