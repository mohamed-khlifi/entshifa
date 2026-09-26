"""Clinic feature response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from ent.core.schemas.base import CamelModel, ORMModel


class ClinicRead(ORMModel):
    public_id: str
    name: str
    legal_name: str | None = None
    slug: str
    default_locale: str
    supported_locales: list[Any]
    timezone: str
    country_code: str
    currency: str
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    tax_id: str | None = None
    registration_number: str | None = None
    logo_attachment_public_id: str | None = None
    settings: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SiteRead(ORMModel):
    public_id: str
    name: str
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class ResolvedSettingRead(CamelModel):
    key: str
    value: Any
    source: Literal["user", "clinic", "system"]


class ClinicalSettingsRead(CamelModel):
    items: list[ResolvedSettingRead]
