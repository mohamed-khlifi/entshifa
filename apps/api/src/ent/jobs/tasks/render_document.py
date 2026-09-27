"""Background job: render a finalized document to PDF (architecture §4)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.features.attachments.models import Attachment
from ent.features.clinics.models import Clinic
from ent.features.documents.html_render import render_from_snapshot
from ent.features.documents.models import Document
from ent.features.patients.models import Patient
from ent.integrations.pdf import get_pdf_renderer
from ent.integrations.storage import get_object_storage
from ent.integrations.storage.keys import build_storage_key
from ent.integrations.storage.malware import scan_bytes
from ent.jobs.base import register_job
from ent.jobs.tasks.media import sha256_hex
from ent.settings import get_settings

JOB_RENDER_DOCUMENT = "jobs.render_document"


@register_job(JOB_RENDER_DOCUMENT, max_attempts=5)
async def render_document(*, document_public_id: str, **_extra: Any) -> dict[str, Any]:
    """Render the frozen snapshot. Template rows are not read again."""

    factory = get_session_factory()
    async with factory() as session:
        document = (
            await session.execute(
                select(Document).where(
                    Document.public_id == document_public_id,
                    Document.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if document is None:
            return {"ok": False, "reason": "not_found"}
        if document.status != "final":
            return {"ok": False, "reason": "not_final"}
        if document.rendered_attachment_id is not None:
            return {"ok": True, "skipped": True}
        snapshot = json.loads(json.dumps(document.content_snapshot))
        if not isinstance(snapshot, dict) or "template" not in snapshot:
            return {"ok": False, "reason": "snapshot"}
        clinic = await session.get(Clinic, int(document.clinic_id))
        patient = await session.get(Patient, int(document.patient_id))
        if clinic is None or patient is None:
            return {"ok": False, "reason": "not_found"}
        clinic_public_id = clinic.public_id
        patient_public_id = patient.public_id
        locale = str(snapshot["template"].get("locale") or document.locale)
        filename = f"{document.category}-{locale}.pdf"
        document_id = int(document.id)
        clinic_id = int(document.clinic_id)
        patient_id = int(document.patient_id)
        created_by_id = document.finalized_by_id

    html = render_from_snapshot(snapshot)
    template = snapshot["template"]
    pdf = get_pdf_renderer().render_pdf(
        html=html,
        css=str(template.get("css") or ""),
        page_setup=dict(template.get("page_setup") or {}),
        direction=str(template.get("direction") or "ltr"),
    )
    scan = scan_bytes(data=pdf, content_type="application/pdf", filename=filename)
    if not scan.clean:
        return {"ok": False, "reason": "malware", "detail": scan.detail}

    settings = get_settings()
    storage = get_object_storage(settings)
    storage_key = build_storage_key(
        clinic_public_id=clinic_public_id,
        patient_public_id=patient_public_id,
        category="document_pdf",
        object_ulid=document_public_id,
        extension="pdf",
    )
    await storage.put_object_bytes(
        key=storage_key,
        data=pdf,
        content_type="application/pdf",
    )

    async with factory() as session:
        current = await session.get(Document, document_id)
        if current is None:
            return {"ok": False, "reason": "not_found"}
        if current.rendered_attachment_id is not None:
            return {"ok": True, "skipped": True}
        existing = (
            await session.execute(
                select(Attachment).where(
                    Attachment.storage_key == storage_key,
                    Attachment.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = Attachment(
                clinic_id=clinic_id,
                patient_id=patient_id,
                patient_public_id=patient_public_id,
                category="document_pdf",
                storage_key=storage_key,
                filename=filename,
                content_type="application/pdf",
                size_bytes=len(pdf),
                checksum_sha256=sha256_hex(pdf),
                is_consented_for_teaching=False,
                processing_status="ready",
                virus_scanned_at=scan.scanned_at,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            session.add(existing)
            await session.flush()
        current.rendered_attachment_id = int(existing.id)
        await session.commit()
        return {
            "ok": True,
            "attachment_public_id": existing.public_id,
            "bytes": len(pdf),
        }
