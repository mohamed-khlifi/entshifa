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


def test_waiting_room_order_compiles_on_mysql() -> None:
    from sqlalchemy import func, select
    from sqlalchemy.dialects import mysql

    from ent.features.scheduling.models import Appointment
    from ent.features.scheduling.repository import _WAITING_ROOM_ORDER

    count = select(func.count()).select_from(
        select(Appointment).order_by(*_WAITING_ROOM_ORDER).subquery()
    )
    sql = str(count.compile(dialect=mysql.dialect()))
    assert "NULLS LAST" not in sql
    assert "NULLS FIRST" not in sql
    assert "arrived_at IS NULL" in sql
