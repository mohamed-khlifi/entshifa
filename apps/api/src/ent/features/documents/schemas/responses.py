"""Document read models."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import CamelModel


class DocumentTemplateRead(CamelModel):
    public_id: str
    code: str
    category: str
    is_system: bool
    is_active: bool


class DocumentRead(CamelModel):
    public_id: str
    patient_public_id: str
    template_code: str
    category: str
    locale: str
    title: str
    status: str
    content_hash: str | None
    finalized_at: datetime | None


class DocumentDownloadRead(CamelModel):
    url: str
    expires_in_seconds: int


class DocumentRecipientRead(CamelModel):
    public_id: str
    recipient_type: str
    name: str
    channel: str
    locale: str | None
    delivery_status: str
