"""Shared clinical value objects reused across features."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import Field

from ent.core.schemas.base import CamelModel


class Laterality(StrEnum):
    RIGHT = "right"
    LEFT = "left"
    BILATERAL = "bilateral"
    MIDLINE = "midline"
    NA = "na"


class CodeableConcept(CamelModel):
    concept_id: str
    code: str | None = None
    system: str | None = None
    display: str | None = None


class Quantity(CamelModel):
    value: Decimal
    unit: str
    system: str | None = None


class Period(CamelModel):
    start: date | datetime | None = None
    end: date | datetime | None = None


class Attachment(CamelModel):
    id: str
    url: str | None = None
    content_type: str | None = None
    title: str | None = None


class Provenance(CamelModel):
    recorded_by: str | None = None
    recorded_at: datetime | None = None
    source: str | None = Field(
        default=None,
        description="clinician|technician|patient|device|ai_confirmed",
    )
    confirmed: bool | None = None
    extras: dict[str, Any] | None = None
