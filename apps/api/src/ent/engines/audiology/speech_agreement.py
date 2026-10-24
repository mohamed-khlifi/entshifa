"""Speech-pure tone agreement check (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from ent.engines.audiology.pta import pure_tone_average
from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import (
    SPEECH_PTA_TOLERANCE_DB,
    PtaFormula,
    ThresholdPoint,
)
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.speech_pta_agreement"
REFERENCE = "Feature specification §8.5 (SRT within about 10 dB of PTA)"
FORMULA = f"flag when |SRT - PTA| > {SPEECH_PTA_TOLERANCE_DB} dB HL"


def speech_discrepancy(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    srt_db: int | None,
    pta_formula: PtaFormula,
) -> bool:
    if srt_db is None:
        return False
    try:
        pta = pure_tone_average(indexed, ear=ear, formula=pta_formula)
    except Exception:
        return False
    return abs(Decimal(srt_db) - pta) > SPEECH_PTA_TOLERANCE_DB


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    ear: str,
    srt_db: int | None,
    pta_formula: PtaFormula,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    discrepancy = speech_discrepancy(
        indexed, ear=ear, srt_db=srt_db, pta_formula=pta_formula
    )
    return CalculationResult(
        code=CODE,
        value="false" if not discrepancy else "true",
        unit=None,
        inputs={"ear": ear, "srt_db": str(srt_db) if srt_db is not None else ""},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(
                "check_reliability",
                {"discrepancy": "true" if discrepancy else "false"},
            ),
        ),
    )
