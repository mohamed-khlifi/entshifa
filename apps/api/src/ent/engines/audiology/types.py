"""Shared audiology engine types (pure data, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

PtaFormula = Literal["3freq", "4freq_who", "high_freq", "fletcher"]
WhoGrade = Literal[
    "normal",
    "mild",
    "moderate",
    "moderately_severe",
    "severe",
    "profound",
    "complete",
]
LossType = Literal["conductive", "sensorineural", "mixed"]
Configuration = Literal[
    "flat",
    "sloping",
    "rising",
    "notched",
    "cookie_bite",
    "precipitous",
    "corner",
]
ShiftRule = Literal["asha", "occupational"]

WHO_GRADE_FREQUENCIES_HZ = (500, 1000, 2000, 4000)
PTA_3_FREQUENCIES_HZ = (500, 1000, 2000)
PTA_HIGH_FREQUENCIES_HZ = (2000, 4000, 8000)
ABG_FREQUENCIES_HZ = (500, 1000, 2000, 4000)
AIR_CONFIG_FREQUENCIES_HZ = (500, 1000, 2000, 4000, 6000, 8000)
ADJACENT_STANDARD_HZ = (500, 1000, 2000, 3000, 4000, 6000, 8000)
OCCUPATIONAL_SHIFT_HZ = (2000, 3000, 4000)
IMPAIRMENT_FREQUENCIES_HZ = (500, 1000, 2000, 3000, 4000)
SPEECH_PTA_TOLERANCE_DB = 10


@dataclass(frozen=True, slots=True)
class ThresholdPoint:
    ear: Literal["right", "left"]
    conduction: Literal["air", "bone"]
    frequency_hz: int
    level_db: int | None
    is_masked: bool
    is_no_response: bool


@dataclass(frozen=True, slots=True)
class AsymmetryRule:
    adjacent_db: int
    adjacent_count: int
    single_db: int
    wrs_percent: int


@dataclass(frozen=True, slots=True)
class SpeechEarInput:
    srt_db: int | None
    wrs_percent: int | None


@dataclass(frozen=True, slots=True)
class AudiogramMetricsResult:
    pta_formula: PtaFormula
    pta_right: Decimal | None
    pta_left: Decimal | None
    abg_right: Decimal | None
    abg_left: Decimal | None
    grade_right: WhoGrade | None
    grade_left: WhoGrade | None
    loss_type_right: LossType | None
    loss_type_left: LossType | None
    configuration_right: Configuration | None
    configuration_left: Configuration | None
    asymmetry_flag: bool
    shift_flag: bool
    engine_version: str
    impairment_right_pct: Decimal | None
    impairment_left_pct: Decimal | None
    impairment_binaural_pct: Decimal | None
    speech_discrepancy_right: bool
    speech_discrepancy_left: bool
