"""UTC helpers for appointment instants (P1-07)."""

from __future__ import annotations

from datetime import UTC, datetime


def to_utc_naive(value: datetime) -> datetime:
    """Persist an aware or naive UTC instant as naive UTC DATETIME(6)."""

    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def as_utc_aware(value: datetime) -> datetime:
    """Interpret stored naive UTC as timezone-aware UTC."""

    if value.tzinfo is not None:
        return value.astimezone(UTC)
    return value.replace(tzinfo=UTC)
