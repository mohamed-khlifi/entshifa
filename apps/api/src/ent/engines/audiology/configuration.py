"""Audiometric configuration description (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from statistics import mean

from ent.engines.audiology.thresholds import index_thresholds, optional_levels
from ent.engines.audiology.types import (
    AIR_CONFIG_FREQUENCIES_HZ,
    Configuration,
    ThresholdPoint,
)
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.configuration"
REFERENCE = "Feature specification §8.5 configuration patterns"
# VERIFY: slope/notch thresholds against clinic protocol prose before narrative use.
FORMULA = (
    "flat: spread <=10 dB; sloping: high mean > low mean +15; rising: low > high +15; "
    "notched: 4 kHz worse than 2 and 8 kHz by >10; cookie-bite: mid > ends +10"
)
_FLAT_SPREAD = 10
_SLOPE_DB = 15
_NOTCH_DB = 10


def describe_configuration(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> tuple[Configuration, tuple[Flag, ...]]:
    air = optional_levels(
        indexed, ear=ear, conduction="air", frequencies_hz=AIR_CONFIG_FREQUENCIES_HZ
    )
    flags: list[Flag] = []
    if len(air) < 3:
        return "flat", tuple(flags)
    values = list(air.values())
    spread = max(values) - min(values)
    low_freqs = [air[f] for f in (500, 1000) if f in air]
    mid_freqs = [air[f] for f in (2000, 4000) if f in air]
    high_freqs = [air[f] for f in (6000, 8000) if f in air]
    low_mean = mean(low_freqs) if low_freqs else None
    mid_mean = mean(mid_freqs) if mid_freqs else None
    high_mean = mean(high_freqs) if high_freqs else None
    if 4000 in air and 2000 in air and 8000 in air:
        if air[4000] - air[2000] > _NOTCH_DB and air[4000] - air[8000] > _NOTCH_DB:
            flags.append(Flag("noise_notch_4k", {"present": "true"}))
            return "notched", tuple(flags)
    if low_mean is not None and high_mean is not None:
        if high_mean - low_mean > _SLOPE_DB:
            return "sloping", tuple(flags)
        if low_mean - high_mean > _SLOPE_DB:
            return "rising", tuple(flags)
    if low_mean is not None and mid_mean is not None and high_mean is not None:
        if mid_mean - low_mean > _NOTCH_DB and mid_mean - high_mean > _NOTCH_DB:
            return "cookie_bite", tuple(flags)
        if high_mean - low_mean > 25:
            return "precipitous", tuple(flags)
        if low_mean < mid_mean and high_mean > mid_mean + _SLOPE_DB:
            return "corner", tuple(flags)
    if spread <= _FLAT_SPREAD:
        return "flat", tuple(flags)
    if low_mean is not None and high_mean is not None and high_mean > low_mean:
        return "sloping", tuple(flags)
    return "flat", tuple(flags)


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    ear: str,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    configuration, flags = describe_configuration(indexed, ear=ear)
    return CalculationResult(
        code=CODE,
        value=configuration,
        unit=None,
        inputs={"ear": ear},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=flags,
    )
