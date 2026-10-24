"""Pure-tone average (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.thresholds import require_levels
from ent.engines.audiology.types import (
    PTA_3_FREQUENCIES_HZ,
    PTA_HIGH_FREQUENCIES_HZ,
    WHO_GRADE_FREQUENCIES_HZ,
    PtaFormula,
    ThresholdPoint,
)
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "audiology.pta"
REFERENCE = "Feature specification §8.5 PTA formula variants"
FORMULA = (
    "3freq: mean(500,1000,2000); 4freq_who: mean(500,1000,2000,4000); "
    "high_freq: mean(2000,4000,8000); fletcher: mean of two lowest of 500,1000,2000"
)
_CENT = Decimal("0.01")


def frequencies_for_formula(formula: PtaFormula) -> tuple[int, ...]:
    if formula == "3freq":
        return PTA_3_FREQUENCIES_HZ
    if formula == "4freq_who":
        return WHO_GRADE_FREQUENCIES_HZ
    if formula == "high_freq":
        return PTA_HIGH_FREQUENCIES_HZ
    if formula == "fletcher":
        return PTA_3_FREQUENCIES_HZ
    raise AudiometryInputError("audiology.invalid_formula")


def pure_tone_average(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    formula: PtaFormula,
) -> Decimal:
    frequencies = frequencies_for_formula(formula)
    levels = require_levels(
        indexed, ear=ear, conduction="air", frequencies_hz=frequencies
    )
    if formula == "fletcher":
        sorted_levels = sorted(levels.values())
        value = (sorted_levels[0] + sorted_levels[1]) / 2
    else:
        value = sum(levels.values()) / len(levels)
    return Decimal(value).quantize(_CENT, rounding=ROUND_HALF_UP)


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    ear: str,
    formula: PtaFormula,
) -> CalculationResult:
    from ent.engines.audiology.thresholds import index_thresholds

    indexed = index_thresholds(thresholds)
    pta = pure_tone_average(indexed, ear=ear, formula=formula)
    freqs = frequencies_for_formula(formula)
    return CalculationResult(
        code=CODE,
        value=str(pta),
        unit="dB HL",
        inputs={
            "ear": ear,
            "formula": formula,
            "frequencies_hz": ",".join(str(f) for f in freqs),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
