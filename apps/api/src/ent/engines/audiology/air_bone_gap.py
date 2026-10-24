"""Air-bone gap per frequency and averaged (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.audiology.thresholds import index_thresholds, optional_levels
from ent.engines.audiology.types import ABG_FREQUENCIES_HZ, ThresholdPoint
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "audiology.air_bone_gap"
REFERENCE = "Feature specification §8.5 air-bone gap"
FORMULA = "ABG(freq)=air(freq)-bone(freq); mean ABG over frequencies with both present"
_CENT = Decimal("0.01")


def gaps_for_ear(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> dict[int, Decimal]:
    air = optional_levels(
        indexed, ear=ear, conduction="air", frequencies_hz=ABG_FREQUENCIES_HZ
    )
    bone = optional_levels(
        indexed, ear=ear, conduction="bone", frequencies_hz=ABG_FREQUENCIES_HZ
    )
    gaps: dict[int, Decimal] = {}
    for frequency_hz in ABG_FREQUENCIES_HZ:
        if frequency_hz not in air or frequency_hz not in bone:
            continue
        gaps[frequency_hz] = Decimal(air[frequency_hz] - bone[frequency_hz]).quantize(
            _CENT, rounding=ROUND_HALF_UP
        )
    return gaps


def average_gap(gaps: Mapping[int, Decimal]) -> Decimal | None:
    if not gaps:
        return None
    total = sum(gaps.values(), start=Decimal(0))
    return (total / len(gaps)).quantize(_CENT, rounding=ROUND_HALF_UP)


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    ear: str,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    gaps = gaps_for_ear(indexed, ear=ear)
    avg = average_gap(gaps)
    return CalculationResult(
        code=CODE,
        value=str(avg) if avg is not None else "",
        unit="dB",
        inputs={
            "ear": ear,
            **{f"abg_{hz}": str(gaps[hz]) for hz in sorted(gaps)},
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
