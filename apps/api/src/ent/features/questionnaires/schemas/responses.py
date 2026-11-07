"""Questionnaire instrument response schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field

from ent.core.schemas.base import CamelModel


class InstrumentOptionRead(CamelModel):
    public_id: str
    value: int
    position: int
    text: str | None = None


class InstrumentItemRead(CamelModel):
    public_id: str
    code: str
    position: int
    subscale: str | None
    is_reverse_scored: bool
    weight: Decimal
    text: str | None = None
    options: list[InstrumentOptionRead] = Field(default_factory=list)


class InstrumentVersionRead(CamelModel):
    public_id: str
    version: str
    effective_from: date
    is_current: bool
    scoring_config: dict[str, object]


class InstrumentSummaryRead(CamelModel):
    public_id: str
    code: str
    category: str
    respondent: str
    scoring_type: str
    min_score: int
    max_score: int
    mcid: Decimal | None
    license_note: str
    reference: str
    is_system: bool
    is_active: bool
    locales_available: list[str] = Field(default_factory=list)


class InstrumentDetailRead(InstrumentSummaryRead):
    current_version: InstrumentVersionRead | None = None
    items: list[InstrumentItemRead] = Field(default_factory=list)


class InstrumentLocalizedRead(InstrumentDetailRead):
    locale: str
    title: str


class InstrumentScoreRead(CamelModel):
    total_score: Decimal
    severity_band: str | None
    subscale_scores: dict[str, Decimal]
    change_from_previous: Decimal | None
    mcid_reached: bool | None
    engine_code: str
    engine_version: str
    reference: str
