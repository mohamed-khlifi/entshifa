"""Allowed appointment status transitions (P1-07)."""

from __future__ import annotations

from ent.features.scheduling.constants import TERMINAL_APPOINTMENT_STATUSES

_ALLOWED: dict[str, frozenset[str]] = {
    "scheduled": frozenset({"arrived", "cancelled", "no_show"}),
    "arrived": frozenset({"in_room", "cancelled", "no_show"}),
    "in_room": frozenset({"completed"}),
}


def can_transition(from_status: str, to_status: str) -> bool:
    if from_status in TERMINAL_APPOINTMENT_STATUSES:
        return False
    return to_status in _ALLOWED.get(from_status, frozenset())
