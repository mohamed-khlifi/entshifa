"""Monaural and binaural hearing impairment percentage (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.audiology.thresholds import optional_levels
from ent.engines.audiology.types import IMPAIRMENT_FREQUENCIES_HZ, ThresholdPoint
from ent.engines.audiology.who_grading import who_pta
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "audiology.impairment"
REFERENCE = (
    "AMA Guides to the Evaluation of Permanent Impairment, 6th ed., Ch. 11; "
    "feature specification §8.5 AMA/AAO-HNS method"
)
# VERIFY: confirm table weights against the clinic's legal template if required.
FORMULA = (
    "monaural % = min(100, max(0, (PTA4-25)*1.5)); binaural % = (5*better + worse) / 6"
)
_CENT = Decimal("0.01")
_PTA_BASE = Decimal("25")
_FACTOR = Decimal("1.5")


def monaural_impairment_percent(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> Decimal | None:
    from ent.engines.audiology.errors import AudiometryInputError

    try:
        pta = who_pta(indexed, ear=ear)
    except AudiometryInputError:
        air = optional_levels(
            indexed,
            ear=ear,
            conduction="air",
            frequencies_hz=IMPAIRMENT_FREQUENCIES_HZ,
        )
        if not air:
            return None
        pta = Decimal(sum(air.values()) / len(air))
    if pta <= _PTA_BASE:
        return Decimal(0).quantize(_CENT, rounding=ROUND_HALF_UP)
    raw = (pta - _PTA_BASE) * _FACTOR
    capped = min(Decimal(100), max(Decimal(0), raw))
    return capped.quantize(_CENT, rounding=ROUND_HALF_UP)


def binaural_impairment_percent(
    right: Decimal | None,
    left: Decimal | None,
) -> Decimal | None:
    if right is None or left is None:
        return None
    better, worse = (right, left) if right <= left else (left, right)
    value = (better * 5 + worse) / 6
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def score_binaural(
    *,
    thresholds: Sequence[ThresholdPoint],
) -> CalculationResult:
    from ent.engines.audiology.thresholds import index_thresholds

    indexed = index_thresholds(thresholds)
    right = monaural_impairment_percent(indexed, ear="right")
    left = monaural_impairment_percent(indexed, ear="left")
    binaural = binaural_impairment_percent(right, left)
    return CalculationResult(
        code=CODE,
        value=str(binaural) if binaural is not None else "",
        unit="%",
        inputs={
            "right_pct": str(right) if right is not None else "",
            "left_pct": str(left) if left is not None else "",
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
