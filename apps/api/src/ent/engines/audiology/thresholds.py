"""Resolve effective air and bone thresholds per ear and frequency."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.types import ThresholdPoint

_EAR = frozenset({"right", "left"})
_COND = frozenset({"air", "bone"})


def index_thresholds(
    points: Sequence[ThresholdPoint],
) -> dict[tuple[str, str, int], ThresholdPoint]:
    """Pick one point per (ear, conduction, frequency); masked wins over unmasked."""

    chosen: dict[tuple[str, str, int], ThresholdPoint] = {}
    for point in points:
        if point.ear not in _EAR or point.conduction not in _COND:
            raise AudiometryInputError("audiology.invalid_threshold", ear=point.ear)
        key = (point.ear, point.conduction, point.frequency_hz)
        existing = chosen.get(key)
        if existing is None:
            chosen[key] = point
            continue
        if point.is_masked and not existing.is_masked:
            chosen[key] = point
    return chosen


def level_db(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    conduction: str,
    frequency_hz: int,
    allow_no_response: bool = False,
) -> int | None:
    point = indexed.get((ear, conduction, frequency_hz))
    if point is None:
        return None
    if point.is_no_response:
        if allow_no_response:
            return point.level_db
        raise AudiometryInputError(
            "audiology.no_response",
            ear=ear,
            frequency_hz=str(frequency_hz),
        )
    if point.level_db is None:
        raise AudiometryInputError(
            "audiology.incomplete_threshold",
            ear=ear,
            frequency_hz=str(frequency_hz),
        )
    return int(point.level_db)


def require_levels(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    conduction: str,
    frequencies_hz: Sequence[int],
) -> dict[int, int]:
    missing: list[int] = []
    values: dict[int, int] = {}
    for frequency_hz in frequencies_hz:
        try:
            value = level_db(
                indexed,
                ear=ear,
                conduction=conduction,
                frequency_hz=frequency_hz,
            )
        except AudiometryInputError:
            missing.append(frequency_hz)
            continue
        if value is None:
            missing.append(frequency_hz)
            continue
        values[frequency_hz] = value
    if missing:
        raise AudiometryInputError(
            "audiology.incomplete_threshold",
            ear=ear,
            frequency_hz=str(missing[0]),
        )
    return values


def optional_levels(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    conduction: str,
    frequencies_hz: Iterable[int],
) -> dict[int, int]:
    values: dict[int, int] = {}
    for frequency_hz in frequencies_hz:
        try:
            value = level_db(
                indexed,
                ear=ear,
                conduction=conduction,
                frequency_hz=frequency_hz,
            )
        except AudiometryInputError:
            continue
        if value is not None:
            values[frequency_hz] = value
    return values
