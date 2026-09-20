"""Clinic and site ORM models (architecture §25.1)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin, GlobalRecordMixin
from ent.core.db.mysql_types import mysql_json, unsigned_bigint


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
    # FK to attachment deferred until P0-13.
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
