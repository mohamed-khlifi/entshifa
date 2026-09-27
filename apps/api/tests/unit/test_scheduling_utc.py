"""UTC conversion helpers for scheduling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from ent.features.scheduling.utc import as_utc_aware, to_utc_naive


def test_to_utc_naive_from_fixed_offset() -> None:
    paris = timezone(timedelta(hours=1))
    local = datetime(2026, 3, 20, 10, 0, tzinfo=paris)
    stored = to_utc_naive(local)
    assert stored.tzinfo is None
    assert stored.hour == 9


def test_as_utc_aware_roundtrip() -> None:
    stored = datetime(2026, 3, 20, 9, 0, 0)
    aware = as_utc_aware(stored)
    assert aware.tzinfo == UTC
