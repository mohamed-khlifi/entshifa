"""Clinic, site and setting ORM models (architecture §25.1 / §25.17)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import (
    AuditMixin,
    ClinicalRecordMixin,
    GlobalRecordMixin,
    PublicIdMixin,
    SoftDeleteMixin,
    SurrogatePkMixin,
    TimestampMixin,
)
from ent.core.db.mysql_types import datetime6, mysql_json, unsigned_bigint

# Architecture §25.17 examples, plus the Phase 1 datasets seed_system records.
REFERENCE_DATASETS: tuple[str, ...] = (
    "formulary",
    "instruments",
    "protocols",
    "terminology",
    "permissions",
    "templates",
    "encounter_templates",
)


class Clinic(GlobalRecordMixin, Base):
    __tablename__ = "clinic"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    slug: Mapped[str] = mapped_column(
        String(80, collation="utf8mb4_0900_as_cs"),
        nullable=False,
        unique=True,
    )
    default_locale: Mapped[str] = mapped_column(String(10), nullable=False)
    supported_locales: Mapped[list[Any]] = mapped_column(mysql_json(), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(160), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(160), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    website: Mapped[str | None] = mapped_column(String(160), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # FK to attachment deferred until logo upload wiring in P1-03.
    logo_attachment_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )
    settings: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    sites: Mapped[list[Site]] = relationship(back_populates="clinic")


class Site(ClinicalRecordMixin, Base):
    __tablename__ = "site"
    __audit_writes__ = True

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(160), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(160), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    clinic: Mapped[Clinic] = relationship(back_populates="sites")


class Setting(GlobalRecordMixin, Base):
    """Scoped clinical / operational settings (architecture §25.17).

    Resolution order: user (clinic_id + user_id) -> clinic (clinic_id, user_id
    NULL) -> system (both NULL). Clinical defaults live only as rows here —
    never as Python fallback literals in engines or services.
    """

    __tablename__ = "setting"
    __audit_writes__ = True

    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(80, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    value: Mapped[Any] = mapped_column(mysql_json(), nullable=False)


class ReferenceDataVersion(
    SurrogatePkMixin,
    PublicIdMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    Base,
):
    """One applied revision of a reference dataset (architecture §25.17 / §28).

    ``version`` is the dataset label (VARCHAR), not the optimistic-lock counter.
    Rows are insert-only, so the integer lock from section 23 is omitted.
    """

    __tablename__ = "reference_data_version"
    __table_args__ = (
        CheckConstraint(
            "dataset IN (" + ",".join(f"'{item}'" for item in REFERENCE_DATASETS) + ")",
            name="ck_reference_data_version__dataset",
        ),
        UniqueConstraint(
            "dataset",
            "version",
            name="uq_reference_data_version__dataset__version",
        ),
        Index("ix_reference_data_version__dataset", "dataset"),
    )

    dataset: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(40, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    applied_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    applied_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
