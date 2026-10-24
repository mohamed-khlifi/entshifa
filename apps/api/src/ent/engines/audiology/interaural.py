"""Interaural threshold difference (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.audiology.pta import pure_tone_average
from ent.engines.audiology.thresholds import index_thresholds, optional_levels
from ent.engines.audiology.types import (
    AIR_CONFIG_FREQUENCIES_HZ,
    PtaFormula,
    ThresholdPoint,
)
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "audiology.interaural_difference"
REFERENCE = "Feature specification §8.5 interaural difference per frequency and PTA"
FORMULA = "|right-left| per frequency; |pta_right-pta_left|"
_CENT = Decimal("0.01")


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    pta_formula: PtaFormula,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    per_freq: dict[str, str] = {}
    for frequency_hz in AIR_CONFIG_FREQUENCIES_HZ:
        right = optional_levels(
            indexed, ear="right", conduction="air", frequencies_hz=(frequency_hz,)
        )
        left = optional_levels(
            indexed, ear="left", conduction="air", frequencies_hz=(frequency_hz,)
        )
        if frequency_hz not in right or frequency_hz not in left:
            continue
        diff = abs(right[frequency_hz] - left[frequency_hz])
        per_freq[str(frequency_hz)] = str(diff)
    try:
        pta_r = pure_tone_average(indexed, ear="right", formula=pta_formula)
        pta_l = pure_tone_average(indexed, ear="left", formula=pta_formula)
        pta_diff = abs(pta_r - pta_l).quantize(_CENT, rounding=ROUND_HALF_UP)
    except Exception:
        pta_diff = None
    return CalculationResult(
        code=CODE,
        value=str(pta_diff) if pta_diff is not None else "",
        unit="dB",
        inputs={**per_freq, "pta_formula": pta_formula},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
