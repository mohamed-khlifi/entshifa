"""Calendar arithmetic for otology follow-up. Intervals come from settings."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class FollowUpPlan:
    tube_first_check_days: int
    tube_first_window_days: int
    tube_interval_months: int
    tube_interval_window_days: int
    wick_removal_days: int
    wick_window_days: int
    cavity_cleaning_months: int
    cavity_window_days: int
    canal_injury_days: int
    canal_injury_window_days: int


def add_months(value: date, months: int) -> date:
    """Move a clinic-local date by a whole number of months, clamping the day."""

    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_days(value: date, days: int) -> date:
    return value + timedelta(days=days)
