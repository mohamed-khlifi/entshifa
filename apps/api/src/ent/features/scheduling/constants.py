"""Scheduling domain constants (architecture §25.4 / P1-07)."""

from __future__ import annotations

from typing import TypedDict

APPOINTMENT_STATUSES: tuple[str, ...] = (
    "scheduled",
    "arrived",
    "in_room",
    "completed",
    "no_show",
    "cancelled",
)

TERMINAL_APPOINTMENT_STATUSES: frozenset[str] = frozenset(
    {"completed", "no_show", "cancelled"},
)

WAITING_ROOM_STATUSES: frozenset[str] = frozenset({"arrived", "in_room"})


class AppointmentTypeSeed(TypedDict):
    code: str
    name_key: str
    default_duration_min: int
    color: str
    requires_room: bool


DEFAULT_APPOINTMENT_TYPES: tuple[AppointmentTypeSeed, ...] = (
    {
        "code": "new_consultation",
        "name_key": "scheduling.appointment_type.new_consultation",
        "default_duration_min": 30,
        "color": "#0d9488",
        "requires_room": False,
    },
    {
        "code": "follow_up",
        "name_key": "scheduling.appointment_type.follow_up",
        "default_duration_min": 20,
        "color": "#2563eb",
        "requires_room": False,
    },
    {
        "code": "procedure",
        "name_key": "scheduling.appointment_type.procedure",
        "default_duration_min": 45,
        "color": "#7c3aed",
        "requires_room": True,
    },
    {
        "code": "audiology_slot",
        "name_key": "scheduling.appointment_type.audiology_slot",
        "default_duration_min": 30,
        "color": "#ea580c",
        "requires_room": True,
    },
    {
        "code": "post_op_check",
        "name_key": "scheduling.appointment_type.post_op_check",
        "default_duration_min": 15,
        "color": "#16a34a",
        "requires_room": False,
    },
    {
        "code": "surgery",
        "name_key": "scheduling.appointment_type.surgery",
        "default_duration_min": 60,
        "color": "#dc2626",
        "requires_room": True,
    },
)
