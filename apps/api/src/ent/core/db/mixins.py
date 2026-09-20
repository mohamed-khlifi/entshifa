"""Reusable ORM column mixins matching architecture section 23."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from ent.core.db.mysql_types import datetime6, unsigned_bigint, unsigned_int
from ent.core.db.types import ULIDType
from ent.core.utils.ids import new_ulid

_CURRENT_TIMESTAMP_6 = text("CURRENT_TIMESTAMP(6)")


class SurrogatePkMixin:
    """Internal BIGINT UNSIGNED auto-increment primary key (never exposed in APIs)."""

    id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        primary_key=True,
        autoincrement=True,
    )


class PublicIdMixin:
    """Public ULID used in URLs and API payloads."""

    public_id: Mapped[str] = mapped_column(
        ULIDType(),
        nullable=False,
        unique=True,
        default=new_ulid,
        insert_default=new_ulid,
    )


class TimestampMixin:
    """created_at / updated_at in UTC DATETIME(6)."""

    created_at: Mapped[datetime] = mapped_column(
        datetime6(),
        nullable=False,
        server_default=_CURRENT_TIMESTAMP_6,
    )
    updated_at: Mapped[datetime] = mapped_column(
        datetime6(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )


class AuditMixin:
    """Who created / last updated the row (FKs deferred; no cascade)."""

    created_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )


class SoftDeleteMixin:
    """Soft delete markers; clinical rows are never hard-deleted by default."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        datetime6(),
        nullable=True,
    )
    deleted_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )


class TenantMixin:
    """clinic_id on every clinical / tenant-scoped table."""

    clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        index=True,
    )


class VersionMixin:
    """Optimistic locking counter."""

    version: Mapped[int] = mapped_column(
        unsigned_int(),
        nullable=False,
        default=1,
        server_default="1",
    )


class ClinicalRecordMixin(
    SurrogatePkMixin,
    PublicIdMixin,
    TenantMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    VersionMixin,
):
    """Full clinical-row column set including tenancy."""


class GlobalRecordMixin(
    SurrogatePkMixin,
    PublicIdMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    VersionMixin,
):
    """Shared columns for non-tenant tables (clinic, user, permission, …)."""
