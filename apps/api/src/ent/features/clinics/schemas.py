"""Clinic and site API schemas."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import ORMModel


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
