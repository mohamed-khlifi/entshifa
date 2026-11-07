"""Questionnaire instrument request schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator

from ent.core.schemas.base import CamelModel
from ent.features.questionnaires.constants import (
    INSTRUMENT_CATEGORIES,
    INSTRUMENT_LOCALES,
    INSTRUMENT_RESPONDENTS,
    INSTRUMENT_SCORING_TYPES,
)

InstrumentCategory = Literal[
    "sinonasal",
    "ear",
    "vertigo",
    "voice",
    "reflux",
    "swallowing",
    "sleep",
    "qol",
    "head_neck",
    "airway",
    "pediatrics",
    "other",
]
InstrumentRespondent = Literal["patient", "clinician", "parent"]
InstrumentScoringType = Literal["sum", "weighted_sum", "custom"]


class InstrumentOptionInput(CamelModel):
    value: int = Field(ge=0, le=100)
    position: int = Field(ge=1, le=50)


class InstrumentItemInput(CamelModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_]+$")
    position: int = Field(ge=1, le=200)
    subscale: str | None = Field(default=None, max_length=40)
    is_reverse_scored: bool = False
    weight: Decimal = Field(default=Decimal("1"), gt=0, le=100)
    options: list[InstrumentOptionInput] | None = None


class SeverityBandInput(CamelModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_]+$")
    min_score: Decimal
    max_score: Decimal


class SubscaleInput(CamelModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_]+$")
    item_codes: list[str] = Field(min_length=1)


class InstrumentScoringConfigInput(CamelModel):
    scale_multiplier: Decimal = Field(default=Decimal("1"), gt=0, le=100)
    subscales: list[SubscaleInput] = Field(default_factory=list)
    reverse_scored_items: list[str] = Field(default_factory=list)
    severity_bands: list[SeverityBandInput] = Field(default_factory=list)
    custom_scorer_code: str | None = Field(default=None, max_length=60)


class InstrumentLocaleTranslationInput(CamelModel):
    locale: str = Field(min_length=2, max_length=10)
    title: str = Field(min_length=1, max_length=500)
    items: dict[str, str] = Field(default_factory=dict)
    options: dict[str, str] = Field(default_factory=dict)

    @field_validator("locale")
    @classmethod
    def _locale_allowed(cls, value: str) -> str:
        if value not in INSTRUMENT_LOCALES:
            msg = "locale"
            raise ValueError(msg)
        return value


class InstrumentSharedOptionInput(CamelModel):
    options: list[InstrumentOptionInput] = Field(min_length=1)


class InstrumentCreate(CamelModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_]+$")
    category: InstrumentCategory
    respondent: InstrumentRespondent
    scoring_type: InstrumentScoringType
    min_score: int = Field(ge=0, le=10000)
    max_score: int = Field(ge=0, le=10000)
    mcid: Decimal | None = Field(default=None, gt=0, le=1000)
    license_note: str = Field(min_length=1, max_length=255)
    reference: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=20)
    effective_from: date
    scoring_config: InstrumentScoringConfigInput
    shared_options: InstrumentSharedOptionInput | None = None
    items: list[InstrumentItemInput] = Field(min_length=1)
    translations: list[InstrumentLocaleTranslationInput] = Field(min_length=1)

    @field_validator("category")
    @classmethod
    def _category(cls, value: str) -> str:
        if value not in INSTRUMENT_CATEGORIES:
            raise ValueError("category")
        return value

    @field_validator("respondent")
    @classmethod
    def _respondent(cls, value: str) -> str:
        if value not in INSTRUMENT_RESPONDENTS:
            raise ValueError("respondent")
        return value

    @field_validator("scoring_type")
    @classmethod
    def _scoring(cls, value: str) -> str:
        if value not in INSTRUMENT_SCORING_TYPES:
            raise ValueError("scoring_type")
        return value


class InstrumentVersionCreate(CamelModel):
    version: str = Field(min_length=1, max_length=20)
    effective_from: date
    is_current: bool = True
    scoring_config: InstrumentScoringConfigInput
    shared_options: InstrumentSharedOptionInput | None = None
    items: list[InstrumentItemInput] = Field(min_length=1)
    translations: list[InstrumentLocaleTranslationInput] = Field(min_length=1)


class InstrumentTranslationUpsert(CamelModel):
    title: str = Field(min_length=1, max_length=500)
    items: dict[str, str] = Field(default_factory=dict)
    options: dict[str, str] = Field(default_factory=dict)


class InstrumentScoreRequest(CamelModel):
    answers: dict[str, int] = Field(min_length=1)
    previous_total_score: Decimal | None = None
    locale: str | None = Field(default=None, min_length=2, max_length=10)
