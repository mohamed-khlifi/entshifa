"""Typed-value rules for an observation row (architecture §25.6)."""

from __future__ import annotations

from ent.engines.observations.types import VALUE_TYPES, ValueDraft

VERSION = "1.0.0"
REFERENCE = (
    "Architecture §25.6 and §26: each finding stores one typed value in its "
    "own column. A finding is a concept id, not free text and not a JSON blob. "
    "Qualifiers hold extra structured attributes only."
)


class ObservationValueError(Exception):
    """The value columns do not match ``value_type``. ``reason`` is a stable token."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def validate_observation_value(value: ValueDraft) -> None:
    """Reject a value whose populated columns do not match its type."""

    if value.value_type not in VALUE_TYPES:
        raise ObservationValueError("value_type")

    text = (value.value_text or "").strip()
    occupied = {
        "concept": value.value_concept_code is not None,
        "numeric": value.value_numeric is not None,
        "boolean": value.value_boolean is not None,
        "text": bool(text),
        "range": value.value_low is not None or value.value_high is not None,
        "ordinal": value.ordinal_value is not None,
    }
    unit_set = value.value_unit is not None and value.value_unit != ""

    if value.value_type == "code":
        _require_only(occupied, "concept")
        if unit_set:
            raise ObservationValueError("value_unit")
        return
    if value.value_type == "numeric":
        _require_only(occupied, "numeric")
        return
    if value.value_type == "boolean":
        _require_only(occupied, "boolean")
        if unit_set:
            raise ObservationValueError("value_unit")
        return
    if value.value_type == "text":
        _require_only(occupied, "text")
        if unit_set:
            raise ObservationValueError("value_unit")
        return
    if value.value_type == "range":
        if value.value_low is None or value.value_high is None:
            raise ObservationValueError("value_range")
        if value.value_low > value.value_high:
            raise ObservationValueError("value_range_order")
        _require_only(occupied, "range")
        return
    _require_only(occupied, "ordinal")
    if unit_set:
        raise ObservationValueError("value_unit")


def _require_only(occupied: dict[str, bool], expected: str) -> None:
    if not occupied[expected]:
        raise ObservationValueError(expected)
    extras = [name for name, is_set in occupied.items() if is_set and name != expected]
    if extras:
        raise ObservationValueError(extras[0])
