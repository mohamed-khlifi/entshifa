"""Clinic letterhead applied around a template at preview and finalization."""

from __future__ import annotations

import base64
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.engines.documents.placeholders import validate_placeholders
from ent.features.attachments.repository import AttachmentRepository
from ent.integrations.storage import get_object_storage
from ent.settings import Settings, get_settings

HEADER_KEY = "documentHeaderHtml"
FOOTER_KEY = "documentFooterHtml"
SIGNATURE_KEY = "documentSignatureAttachmentPublicId"

LETTERHEAD_PLACEHOLDERS = frozenset(
    {
        "clinic.name",
        "clinic.phone",
        "clinic.address",
        "clinic.email",
        "document.issuedOn",
    }
)

_MAX_IMAGE_BYTES = 1_500_000


def validate_letterhead_html(html: str) -> None:
    """Reject letterhead that names a placeholder the clinic block does not own."""

    issue = validate_placeholders((html,), set(LETTERHEAD_PLACEHOLDERS))
    if issue is None:
        return
    if issue.reason == "undeclared":
        raise ValidationError(reason="placeholder", name=issue.name)
    raise ValidationError(reason="template_syntax")


async def validate_document_settings(
    session: AsyncSession,
    *,
    clinic_id: int,
    settings: dict[str, Any],
) -> None:
    for key in (HEADER_KEY, FOOTER_KEY):
        value = settings.get(key)
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            raise ValidationError(reason="placeholder", name=key)
        validate_letterhead_html(value)
    signature_id = settings.get(SIGNATURE_KEY)
    if signature_id is None or signature_id == "":
        return
    if not isinstance(signature_id, str):
        raise ValidationError(reason="signature")
    attachment = await AttachmentRepository(
        session, clinic_id=clinic_id
    ).get_by_public_id(signature_id)
    if attachment is None or attachment.category != "signature":
        raise NotFoundError(resource="attachment", public_id=signature_id)


def sample_placeholder_data(placeholders: dict[str, Any]) -> dict[str, Any]:
    """Nested values so a live preview can render without a patient row."""

    data: dict[str, Any] = {}
    for path, spec in placeholders.items():
        kind = spec.get("type") if isinstance(spec, dict) else "string"
        if kind in {"text_list", "code_list"}:
            value: Any = []
        elif kind == "integer":
            value = 0
        elif kind == "date":
            value = "2000-01-01"
        else:
            value = ""
        _assign(data, str(path), value)
    return data


async def compose_letterhead(
    session: AsyncSession,
    *,
    clinic_id: int,
    clinic: Any,
    header_html: str,
    footer_html: str,
    settings: Settings | None = None,
) -> tuple[str, str]:
    """Prefix the clinic header and append footer and signature images."""

    raw = clinic.settings if isinstance(getattr(clinic, "settings", None), dict) else {}
    extra_header = raw.get(HEADER_KEY) if isinstance(raw.get(HEADER_KEY), str) else ""
    extra_footer = raw.get(FOOTER_KEY) if isinstance(raw.get(FOOTER_KEY), str) else ""
    app_settings = settings or get_settings()
    logo = await _embed_image(
        session,
        clinic_id=clinic_id,
        attachment_id=getattr(clinic, "logo_attachment_id", None),
        settings=app_settings,
    )
    signature_key = raw.get(SIGNATURE_KEY)
    signature = ""
    if isinstance(signature_key, str) and signature_key:
        signature = await _embed_public_image(
            session,
            clinic_id=clinic_id,
            public_id=signature_key,
            settings=app_settings,
        )
    return (
        f"{logo}{extra_header}{header_html}",
        f"{footer_html}{signature}{extra_footer}",
    )


def _assign(data: dict[str, Any], path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = value


async def _embed_public_image(
    session: AsyncSession,
    *,
    clinic_id: int,
    public_id: str,
    settings: Settings,
) -> str:
    attachment = await AttachmentRepository(
        session, clinic_id=clinic_id
    ).get_by_public_id(public_id)
    if attachment is None:
        return ""
    return await _embed_attachment(attachment, settings)


async def _embed_image(
    session: AsyncSession,
    *,
    clinic_id: int,
    attachment_id: int | None,
    settings: Settings,
) -> str:
    if attachment_id is None:
        return ""
    attachment = await AttachmentRepository(session, clinic_id=clinic_id).get(
        int(attachment_id)
    )
    if attachment is None:
        return ""
    return await _embed_attachment(attachment, settings)


async def _embed_attachment(attachment: Any, settings: Settings) -> str:
    content_type = str(getattr(attachment, "content_type", ""))
    if not content_type.startswith("image/"):
        return ""
    storage = get_object_storage(settings)
    raw = await storage.get_object_bytes(key=str(attachment.storage_key))
    if len(raw) > _MAX_IMAGE_BYTES:
        return ""
    encoded = base64.b64encode(raw).decode("ascii")
    return (
        '<p class="letterhead-image">'
        f'<img src="data:{content_type};base64,{encoded}" alt="">'
        "</p>"
    )
