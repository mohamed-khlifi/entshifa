"""Unit tests for attachment service helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from ent.core.schemas.common import CodeableConcept
from ent.features.attachments.models import Attachment, MediaVariant
from ent.features.attachments.service import _extension_for, _to_read, _to_utc_naive


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
    attachment.laterality = "left"
    attachment.is_consented_for_teaching = True
    site = CodeableConcept(
        concept_id="01ARZ3NDEKTSV4RRFFQ69G5FB3", code="ear", display="Ear"
    )
    read = _to_read(attachment, body_site=site)
    assert len(read.variants) == 1
    assert read.variants[0].variant == "thumb"
    assert read.is_consented_for_teaching is True
    assert read.laterality == "left"
    assert read.body_site is not None
    assert read.body_site.display == "Ear"


def test_to_utc_naive_converts_aware_instants() -> None:
    aware = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
    assert _to_utc_naive(aware).tzinfo is None
    assert _to_utc_naive(aware) == datetime(2026, 9, 27, 12, 0)
