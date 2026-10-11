"""Clinic-local recall dates and timeline cursors."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ent.features.patients.timeline_repository import (
    decode_timeline_cursor,
    encode_timeline_cursor,
)
from ent.features.recalls.dates import (
    clinic_local_date,
    due_on_from_interval,
    effective_status,
)


def test_due_date_is_a_clinic_local_calendar_date() -> None:
    # 2026-03-29 23:30 UTC is already 30 March in Paris.
    instant = datetime(2026, 3, 29, 23, 30, tzinfo=UTC)
    today = clinic_local_date(instant, "Europe/Paris")
    assert today.isoformat() == "2026-03-30"
    assert due_on_from_interval(today, 42).isoformat() == "2026-05-11"


def test_pending_past_the_window_reads_as_overdue() -> None:
    due = due_on_from_interval(
        clinic_local_date(datetime(2026, 1, 1, tzinfo=UTC), "Europe/Paris"), 0
    )
    assert (
        effective_status(status="pending", due_on=due, window_days=14, today=due)
        == "pending"
    )
    later = due_on_from_interval(due, 15)
    assert (
        effective_status(status="pending", due_on=due, window_days=14, today=later)
        == "overdue"
    )
    assert (
        effective_status(status="booked", due_on=due, window_days=14, today=later)
        == "booked"
    )


def test_unknown_timezone_is_rejected() -> None:
    with pytest.raises(ValueError):
        clinic_local_date(datetime(2026, 1, 1, tzinfo=UTC), "Not/AZone")


def test_timeline_cursor_round_trip() -> None:
    occurred = datetime(2026, 4, 2, 9, 15, 1, 250000)
    encoded = encode_timeline_cursor(
        occurred, "consultation", "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    )
    assert decode_timeline_cursor(encoded) == (
        occurred,
        "consultation",
        "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    )
