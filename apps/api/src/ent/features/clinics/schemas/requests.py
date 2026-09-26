"""Clinic feature request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from ent.core.schemas.base import CamelModel


class ClinicUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    legal_name: str | None = Field(default=None, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=80)
    default_locale: str | None = Field(default=None, min_length=2, max_length=10)
    supported_locales: list[str] | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    address_line1: str | None = Field(default=None, max_length=160)
    address_line2: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=160)
    tax_id: str | None = Field(default=None, max_length=40)
    registration_number: str | None = Field(default=None, max_length=40)
    settings: dict[str, Any] | None = None
    is_active: bool | None = None

    @field_validator("country_code")
    @classmethod
    def country_upper(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @field_validator("slug")
    @classmethod
    def slug_normalized(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if not cleaned.replace("-", "").isalnum():
            msg = "slug must be alphanumeric with hyphens"
            raise ValueError(msg)
        return cleaned


class SiteCreate(CamelModel):
    name: str = Field(min_length=1, max_length=160)
    address_line1: str | None = Field(default=None, max_length=160)
    address_line2: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=32)
    is_primary: bool = False


class SiteUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    address_line1: str | None = Field(default=None, max_length=160)
    address_line2: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=32)
    is_primary: bool | None = None


class ClinicalSettingItem(CamelModel):
    key: str = Field(min_length=1, max_length=80)
    value: Any


class ClinicalSettingsPut(CamelModel):
    """Replace or upsert clinic-scoped clinical settings."""

    items: list[ClinicalSettingItem] = Field(min_length=1)
