"""Completed civil age for document snapshots.

This is calendar arithmetic, not a clinical score or dosing input.
"""

from __future__ import annotations

from datetime import date

VERSION = "1.0.0"
REFERENCE = (
    "Completed years and months between two civil dates. "
    "The anniversary month and day must have been reached."
)


def completed_age(birth_date: date, on_date: date) -> tuple[int, int]:
    """Return completed years and completed months. Raises if on_date is earlier."""

    if on_date < birth_date:
        raise ValueError("documents.age_before_birth")
    years = on_date.year - birth_date.year
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    months = (on_date.year - birth_date.year) * 12 + on_date.month - birth_date.month
    if on_date.day < birth_date.day:
        months -= 1
    return years, months
