"""Unit tests for attachment service helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from ent.features.attachments.models import Attachment, MediaVariant
from ent.features.attachments.service import _extension_for, _to_read


def test_extension_for_filename_and_content_type() -> None:
    assert _extension_for("scan.PDF", "application/pdf") == "pdf"
    assert _extension_for("photo", "image/png") == "png"
    assert _extension_for("file", "application/octet-stream") == "bin"


def test_to_read_skips_deleted_variants() -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    attachment = Attachment(
        clinic_id=1,
        public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        category="clinical_photo",
        storage_key="k",
        filename="a.jpg",
        content_type="image/jpeg",
        size_bytes=10,
        processing_status="ready",
        created_at=now,
        updated_at=now,
    )
    live = MediaVariant(
        clinic_id=1,
        public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        attachment_id=1,
        variant="thumb",
        storage_key="k-t",
        content_type="image/jpeg",
        size_bytes=5,
        width=10,
        height=10,
        created_at=now,
        updated_at=now,
    )
    deleted = MediaVariant(
        clinic_id=1,
        public_id="01ARZ3NDEKTSV4RRFFQ69G5FB2",
        attachment_id=1,
        variant="preview",
        storage_key="k-p",
        content_type="image/jpeg",
        size_bytes=5,
        width=20,
        height=20,
        deleted_at=now,
        created_at=now,
        updated_at=now,
    )
    attachment.variants = [live, deleted]
    read = _to_read(attachment)
    assert len(read.variants) == 1
    assert read.variants[0].variant == "thumb"
