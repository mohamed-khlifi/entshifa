"""User, membership and session ORM models (architecture §25.1)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin, GlobalRecordMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint, varbinary
from ent.core.db.types import EncryptedString


class User(GlobalRecordMixin, Base):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(
        String(190, collation="utf8mb4_0900_as_cs"),
        nullable=False,
        unique=True,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        datetime6(),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(
        datetime6(),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str | None] = mapped_column(String(40), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(80), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # FK to attachment deferred until P0-13.
    signature_attachment_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )
    preferred_locale: Mapped[str] = mapped_column(String(10), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        datetime6(),
        nullable=True,
    )
    failed_login_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    clinic_roles: Mapped[list[UserClinicRole]] = relationship(back_populates="user")
    sessions: Mapped[list[UserSession]] = relationship(back_populates="user")


class UserClinicRole(ClinicalRecordMixin, Base):
    __tablename__ = "user_clinic_role"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "clinic_id",
            "role_id",
            name="uq_user_clinic_role__user_id__clinic_id__role_id",
        ),
        Index("ix_user_clinic_role__clinic_id__user_id", "clinic_id", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("role.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    site_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("site.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(back_populates="clinic_roles")


class UserSession(GlobalRecordMixin, Base):
    __tablename__ = "user_session"
    __table_args__ = (
        Index("ix_user_session__user_id__expires_at", "user_id", "expires_at"),
    )

    user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(64, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    device_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[bytes | None] = mapped_column(varbinary(16), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    session_family_id: Mapped[str] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    previous_refresh_token_hash: Mapped[str | None] = mapped_column(
        String(64, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )
    active_clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="sessions")
