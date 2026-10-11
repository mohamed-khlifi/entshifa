"""Clinic-local due dates for manual recalls.

Due dates are calendar dates in the clinic timezone, not UTC timestamps.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def clinic_local_date(now: datetime, timezone_name: str) -> date:
    """Calendar date in the clinic timezone."""

    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(timezone_name) from exc
    instant = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
    return instant.astimezone(zone).date()


def due_on_from_interval(today: date, interval_days: int) -> date:
    return today + timedelta(days=interval_days)


def window_end(due_on: date, window_days: int) -> date:
    return due_on + timedelta(days=window_days)


def effective_status(
    *,
    status: str,
    due_on: date,
    window_days: int,
    today: date,
) -> str:
    """Pending recalls past the window read as overdue. Stored status stays pending."""

    if status == "pending" and today > window_end(due_on, window_days):
        return "overdue"
    return status
