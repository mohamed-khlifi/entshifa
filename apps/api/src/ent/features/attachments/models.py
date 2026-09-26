"""Attachment and media_variant ORM models (architecture §25.16 / P0-13)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint
from ent.core.db.types import LateralityType

ATTACHMENT_CATEGORIES = (
    "endoscopy_image",
    "endoscopy_video",
    "clinical_photo",
    "audiogram_scan",
    "imaging_report",
    "pathology",
    "external_letter",
    "document_pdf",
    "signature",
    "logo",
    "voice_recording",
)

MEDIA_VARIANTS = ("thumb", "preview", "web", "print")

# Categories whose uploads are treated as clinical images (EXIF strip required).
IMAGE_CATEGORIES = frozenset(
    {
        "endoscopy_image",
        "clinical_photo",
        "audiogram_scan",
        "signature",
        "logo",
    },
)


class Attachment(ClinicalRecordMixin, Base):
    """Clinical/media object stored in object storage (never a public URL)."""

    __tablename__ = "attachment"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            "category IN ("
            + ",".join(f"'{c}'" for c in ATTACHMENT_CATEGORIES)
            + ")",
            name="ck_attachment__category",
        ),
        CheckConstraint(
            "laterality IS NULL OR laterality IN "
            "('right','left','bilateral','midline','na')",
            name="ck_attachment__laterality",
        ),
        Index(
            "ix_attachment__clinic_id__patient_id__category__captured_at",
            "clinic_id",
            "patient_id",
            "category",
            "captured_at",
        ),
        Index("ix_attachment__clinic_id__storage_key", "clinic_id", "storage_key", unique=True),
    )

    # patient_id is nullable until the patients feature lands; FK deferred.
    patient_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    encounter_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    procedure_record_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)

    category: Mapped[str] = mapped_column(String(40), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(400), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(unsigned_bigint(), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )
    width: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    height: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    body_site_concept_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    laterality: Mapped[str | None] = mapped_column(LateralityType(), nullable=True)
    map_region_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    captured_by_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    device: Mapped[str | None] = mapped_column(String(80), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_consented_for_teaching: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    virus_scanned_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    # Public id of the patient when known (no FK until patients feature).
    patient_public_id: Mapped[str | None] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )

    variants: Mapped[list[MediaVariant]] = relationship(
        "MediaVariant",
        back_populates="attachment",
        lazy="selectin",
    )


class MediaVariant(ClinicalRecordMixin, Base):
    """Derived representation of an attachment (thumb, preview, web, print)."""

    __tablename__ = "media_variant"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            "variant IN ('thumb','preview','web','print')",
            name="ck_media_variant__variant",
        ),
        Index(
            "uq_media_variant__attachment_id__variant",
            "attachment_id",
            "variant",
            unique=True,
        ),
        Index("ix_media_variant__clinic_id", "clinic_id"),
    )

    attachment_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("attachment.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    variant: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(400), nullable=False)
    width: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    height: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    size_bytes: Mapped[int] = mapped_column(unsigned_bigint(), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    attachment: Mapped[Attachment] = relationship("Attachment", back_populates="variants")
