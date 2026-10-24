"""WHO 2021 hearing impairment grades (feature spec §8.5, appendix A)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from ent.engines.audiology.pta import pure_tone_average
from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import ThresholdPoint, WhoGrade
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "audiology.who_grade"
REFERENCE = "WHO 2021 grades of hearing impairment; appendix A PTA 0.5,1,2,4 kHz"
FORMULA = (
    "normal <20; mild 20-<35; moderate 35-<50; moderately_severe 50-<65; "
    "severe 65-<80; profound 80-<95; complete >=95 dB HL (4-frequency PTA)"
)


def grade_from_pta(pta: Decimal) -> WhoGrade:
    value = float(pta)
    if value < 20:
        return "normal"
    if value < 35:
        return "mild"
    if value < 50:
        return "moderate"
    if value < 65:
        return "moderately_severe"
    if value < 80:
        return "severe"
    if value < 95:
        return "profound"
    return "complete"


def who_pta(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> Decimal:
    return pure_tone_average(indexed, ear=ear, formula="4freq_who")


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    ear: str,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    pta = who_pta(indexed, ear=ear)
    grade = grade_from_pta(pta)
    return CalculationResult(
        code=CODE,
        value=grade,
        unit=None,
        inputs={"ear": ear, "pta_db": str(pta)},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
