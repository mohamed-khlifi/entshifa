"""Audit and access log ORM models (architecture section 25.17)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from ent.core.db.base import Base
from ent.core.db.mixins import SurrogatePkMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint, varbinary
from ent.core.db.types import ULIDType
from ent.core.utils.ids import new_ulid


class AuditLog(SurrogatePkMixin, Base):
    """Write-side audit trail (create/update/delete/sign/login/…)."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log__clinic_id__occurred_at", "clinic_id", "occurred_at"),
        Index(
            "ix_audit_log__clinic_id__user_id__occurred_at",
            "clinic_id",
            "user_id",
            "occurred_at",
        ),
        Index("ix_audit_log__entity_type__entity_id", "entity_type", "entity_id"),
        Index(
            "ix_audit_log__clinic_id__patient_id__occurred_at",
            "clinic_id",
            "patient_id",
            "occurred_at",
        ),
    )

    public_id: Mapped[str] = mapped_column(
        ULIDType(),
        nullable=False,
        unique=True,
        default=new_ulid,
        insert_default=new_ulid,
    )
    clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    entity_public_id: Mapped[str | None] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )
    patient_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[bytes | None] = mapped_column(varbinary(16), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)


class AccessLog(SurrogatePkMixin, Base):
    """Read-side access trail (chart opened, document viewed, …)."""

    __tablename__ = "access_log"
    __table_args__ = (
        Index("ix_access_log__clinic_id__occurred_at", "clinic_id", "occurred_at"),
        Index(
            "ix_access_log__clinic_id__user_id__occurred_at",
            "clinic_id",
            "user_id",
            "occurred_at",
        ),
        Index("ix_access_log__entity_type__entity_id", "entity_type", "entity_id"),
        Index(
            "ix_access_log__clinic_id__patient_id__occurred_at",
            "clinic_id",
            "patient_id",
            "occurred_at",
        ),
    )

    public_id: Mapped[str] = mapped_column(
        ULIDType(),
        nullable=False,
        unique=True,
        default=new_ulid,
        insert_default=new_ulid,
    )
    clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    entity_public_id: Mapped[str | None] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )
    patient_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[bytes | None] = mapped_column(varbinary(16), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
