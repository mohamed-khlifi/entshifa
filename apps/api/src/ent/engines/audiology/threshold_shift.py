"""Significant threshold shift vs baseline (feature spec §8.5, appendix A)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import (
    ADJACENT_STANDARD_HZ,
    OCCUPATIONAL_SHIFT_HZ,
    ShiftRule,
    ThresholdPoint,
)
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.threshold_shift"
REFERENCE = (
    "ASHA ototoxicity criteria; appendix A ASHA threshold shift; "
    "occupational STS average 10 dB at 2,3,4 kHz (feature spec §8.5)"
)
FORMULA = (
    "asha: 20 dB worse at one frequency, or 10 dB at two adjacent, or "
    "no response at three consecutive where baseline had response; "
    "occupational: mean worsening >=10 dB at 2000,3000,4000 Hz"
)


def _worsening(current: int | None, baseline: int | None) -> int | None:
    if current is None or baseline is None:
        return None
    return current - baseline


def _point_level(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    frequency_hz: int,
) -> tuple[int | None, bool]:
    point = indexed.get((ear, "air", frequency_hz))
    if point is None:
        return None, False
    if point.is_no_response:
        return point.level_db, True
    return point.level_db, False


def shift_asha(
    current: Mapping[tuple[str, str, int], ThresholdPoint],
    baseline: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> bool:
    for frequency_hz in ADJACENT_STANDARD_HZ:
        cur, cur_nr = _point_level(current, ear=ear, frequency_hz=frequency_hz)
        base, base_nr = _point_level(baseline, ear=ear, frequency_hz=frequency_hz)
        if cur is not None and base is not None and not cur_nr and not base_nr:
            if cur - base >= 20:
                return True
    freqs = list(ADJACENT_STANDARD_HZ)
    for index in range(len(freqs) - 1):
        low_hz, high_hz = freqs[index], freqs[index + 1]
        cur_low, nr_low = _point_level(current, ear=ear, frequency_hz=low_hz)
        base_low, _ = _point_level(baseline, ear=ear, frequency_hz=low_hz)
        cur_high, nr_high = _point_level(current, ear=ear, frequency_hz=high_hz)
        base_high, _ = _point_level(baseline, ear=ear, frequency_hz=high_hz)
        if (
            cur_low is None
            or base_low is None
            or cur_high is None
            or base_high is None
        ):
            continue
        if nr_low or nr_high:
            continue
        if cur_low - base_low >= 10 and cur_high - base_high >= 10:
            return True
    consecutive_nr = 0
    for frequency_hz in ADJACENT_STANDARD_HZ:
        cur, cur_nr = _point_level(current, ear=ear, frequency_hz=frequency_hz)
        base, base_nr = _point_level(baseline, ear=ear, frequency_hz=frequency_hz)
        if cur_nr and base is not None and not base_nr:
            consecutive_nr += 1
            if consecutive_nr >= 3:
                return True
        else:
            consecutive_nr = 0
    return False


def shift_occupational(
    current: Mapping[tuple[str, str, int], ThresholdPoint],
    baseline: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> bool:
    shifts: list[int] = []
    for frequency_hz in OCCUPATIONAL_SHIFT_HZ:
        cur, cur_nr = _point_level(current, ear=ear, frequency_hz=frequency_hz)
        base, base_nr = _point_level(baseline, ear=ear, frequency_hz=frequency_hz)
        if cur is None or base is None or cur_nr or base_nr:
            continue
        shifts.append(cur - base)
    if len(shifts) != len(OCCUPATIONAL_SHIFT_HZ):
        return False
    return sum(shifts) / len(shifts) >= 10


def significant_shift(
    current: Sequence[ThresholdPoint],
    baseline: Sequence[ThresholdPoint],
    *,
    rule: ShiftRule,
) -> bool:
    cur_index = index_thresholds(current)
    base_index = index_thresholds(baseline)
    for ear in ("right", "left"):
        if rule == "asha":
            if shift_asha(cur_index, base_index, ear=ear):
                return True
        elif shift_occupational(cur_index, base_index, ear=ear):
            return True
    return False


def score(
    *,
    current: Sequence[ThresholdPoint],
    baseline: Sequence[ThresholdPoint],
    rule: ShiftRule,
) -> CalculationResult:
    met = significant_shift(current, baseline, rule=rule)
    return CalculationResult(
        code=CODE,
        value="true" if met else "false",
        unit=None,
        inputs={"rule": rule},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(Flag("threshold_shift_met", {"met": "true" if met else "false"}),),
    )
