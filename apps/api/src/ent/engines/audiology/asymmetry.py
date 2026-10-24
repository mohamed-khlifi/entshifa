"""Asymmetry criterion (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Sequence

from ent.engines.audiology.thresholds import index_thresholds, optional_levels
from ent.engines.audiology.types import (
    ADJACENT_STANDARD_HZ,
    AsymmetryRule,
    ThresholdPoint,
)
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.asymmetry"
REFERENCE = "Feature specification §8.5 asymmetry criterion"
FORMULA = (
    "flag when interaural difference >= adjacent_db at adjacent_count adjacent "
    "frequencies, or >= single_db at one frequency, or WRS difference >= wrs_percent"
)


def _adjacent_pairs() -> list[tuple[int, int]]:
    freqs = list(ADJACENT_STANDARD_HZ)
    return [(freqs[i], freqs[i + 1]) for i in range(len(freqs) - 1)]


def asymmetry_met(
    indexed: dict[tuple[str, str, int], ThresholdPoint],
    *,
    rule: AsymmetryRule,
    speech_right: int | None = None,
    speech_left: int | None = None,
) -> bool:
    for frequency_hz in ADJACENT_STANDARD_HZ:
        right = optional_levels(
            indexed, ear="right", conduction="air", frequencies_hz=(frequency_hz,)
        )
        left = optional_levels(
            indexed, ear="left", conduction="air", frequencies_hz=(frequency_hz,)
        )
        if frequency_hz not in right or frequency_hz not in left:
            continue
        if abs(right[frequency_hz] - left[frequency_hz]) >= rule.single_db:
            return True
    adjacent_hits = 0
    for low_hz, high_hz in _adjacent_pairs():
        right_low = optional_levels(
            indexed, ear="right", conduction="air", frequencies_hz=(low_hz,)
        )
        left_low = optional_levels(
            indexed, ear="left", conduction="air", frequencies_hz=(low_hz,)
        )
        right_high = optional_levels(
            indexed, ear="right", conduction="air", frequencies_hz=(high_hz,)
        )
        left_high = optional_levels(
            indexed, ear="left", conduction="air", frequencies_hz=(high_hz,)
        )
        if low_hz not in right_low or low_hz not in left_low:
            continue
        if high_hz not in right_high or high_hz not in left_high:
            continue
        if (
            abs(right_low[low_hz] - left_low[low_hz]) >= rule.adjacent_db
            and abs(right_high[high_hz] - left_high[high_hz]) >= rule.adjacent_db
        ):
            adjacent_hits += 1
    if adjacent_hits >= rule.adjacent_count:
        return True
    if (
        speech_right is not None
        and speech_left is not None
        and abs(speech_right - speech_left) >= rule.wrs_percent
    ):
        return True
    return False


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    rule: AsymmetryRule,
    speech_right: int | None = None,
    speech_left: int | None = None,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    met = asymmetry_met(
        indexed,
        rule=rule,
        speech_right=speech_right,
        speech_left=speech_left,
    )
    return CalculationResult(
        code=CODE,
        value="true" if met else "false",
        unit=None,
        inputs={
            "adjacent_db": str(rule.adjacent_db),
            "adjacent_count": str(rule.adjacent_count),
            "single_db": str(rule.single_db),
            "wrs_percent": str(rule.wrs_percent),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(Flag("asymmetry_criterion_met", {"met": "true" if met else "false"}),),
    )
