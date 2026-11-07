"""Typed inputs and outputs for questionnaire scoring."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from ent.engines.results import CalculationResult

ScoringType = Literal["sum", "weighted_sum"]


@dataclass(frozen=True, slots=True)
class InstrumentItemSpec:
    code: str
    position: int
    allowed_values: tuple[int, ...]
    subscale: str | None = None
    is_reverse_scored: bool = False
    weight: Decimal = Decimal("1")


@dataclass(frozen=True, slots=True)
class SeverityBandSpec:
    code: str
    min_score: Decimal
    max_score: Decimal


@dataclass(frozen=True, slots=True)
class SubscaleSpec:
    code: str
    item_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InstrumentScoringSpec:
    code: str
    version: str
    scoring_type: ScoringType
    min_score: Decimal
    max_score: Decimal
    reference: str
    items: tuple[InstrumentItemSpec, ...]
    subscales: tuple[SubscaleSpec, ...] = ()
    severity_bands: tuple[SeverityBandSpec, ...] = ()
    scale_multiplier: Decimal = Decimal("1")
    mcid: Decimal | None = None


@dataclass(frozen=True, slots=True)
class QuestionnaireScoreOutput:
    calculation: CalculationResult
    total_score: Decimal
    item_scores: Mapping[str, Decimal]
    subscale_scores: Mapping[str, Decimal]
    severity_band: str | None
    change_from_previous: Decimal | None
    mcid_reached: bool | None
