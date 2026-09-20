"""Role and permission ORM models (architecture §25.1)."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import GlobalRecordMixin
from ent.core.db.mysql_types import unsigned_bigint


class Permission(GlobalRecordMixin, Base):
    __tablename__ = "permission"

    code: Mapped[str] = mapped_column(
        String(80, collation="utf8mb4_0900_as_cs"),
        nullable=False,
        unique=True,
    )
    group_code: Mapped[str] = mapped_column(String(40), nullable=False)

    role_links: Mapped[list[RolePermission]] = relationship(back_populates="permission")


class Role(GlobalRecordMixin, Base):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role__clinic_id__code", "clinic_id", "code"),
    )

    # NULL = system role; not TenantMixin (clinic_id is optional).
    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(
        String(40, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    name_key: Mapped[str] = mapped_column(String(80), nullable=False)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    permission_links: Mapped[list[RolePermission]] = relationship(back_populates="role")


class RolePermission(GlobalRecordMixin, Base):
    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission__role_id__permission_id",
        ),
    )

    role_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("role.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    permission_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("permission.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )

    role: Mapped[Role] = relationship(back_populates="permission_links")
    permission: Mapped[Permission] = relationship(back_populates="role_links")
