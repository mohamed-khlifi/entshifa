"""Attachment response schemas."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import CamelModel


class PresignedUrlResponse(CamelModel):
    url: str
    method: str
    expires_in_seconds: int
    headers: dict[str, str]


class AttachmentUploadUrlResponse(CamelModel):
    upload_token: str
    storage_key: str
    upload: PresignedUrlResponse


class MediaVariantRead(CamelModel):
    public_id: str
    variant: str
    width: int | None
    height: int | None
    size_bytes: int
    content_type: str


class AttachmentRead(CamelModel):
    public_id: str
    category: str
    filename: str
    content_type: str
    size_bytes: int
    checksum_sha256: str | None
    width: int | None
    height: int | None
    duration_ms: int | None
    caption: str | None
    processing_status: str
    patient_public_id: str | None
    virus_scanned_at: datetime | None
    captured_at: datetime | None
    variants: list[MediaVariantRead]


class AttachmentDownloadUrlResponse(CamelModel):
    attachment_public_id: str
    variant: str | None
    download: PresignedUrlResponse
