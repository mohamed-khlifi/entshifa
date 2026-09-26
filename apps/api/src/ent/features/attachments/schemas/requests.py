"""Attachment request schemas."""

from __future__ import annotations

from pydantic import Field, field_validator

from ent.core.schemas.base import CamelModel
from ent.features.attachments.models import ATTACHMENT_CATEGORIES

_ALLOWED_CATEGORIES = frozenset(ATTACHMENT_CATEGORIES)


class AttachmentUploadUrlRequest(CamelModel):
    """Client asks for a pre-signed PUT URL; file bytes never hit the API."""

    category: str = Field(min_length=3, max_length=40)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=100)
    size_bytes: int = Field(ge=1, le=2_147_483_648)  # 2 GiB hard cap
    patient_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    caption: str | None = Field(default=None, max_length=255)

    @field_validator("category")
    @classmethod
    def category_allowed(cls, value: str) -> str:
        if value not in _ALLOWED_CATEGORIES:
            msg = "unsupported attachment category"
            raise ValueError(msg)
        return value

    @field_validator("filename")
    @classmethod
    def filename_safe(cls, value: str) -> str:
        name = value.strip().replace("\\", "/").split("/")[-1]
        if not name or name in {".", ".."}:
            msg = "invalid filename"
            raise ValueError(msg)
        return name


class AttachmentConfirmRequest(CamelModel):
    """Confirm that the client finished uploading to object storage."""

    upload_token: str = Field(min_length=26, max_length=26)
