"""Inclusive day count for a sick-leave certificate."""

from __future__ import annotations

from datetime import date

VERSION = "1.0.0"
REFERENCE = (
    "A sick-leave period includes both the start date and the end date "
    "(feature specification §14.3)."
)


def inclusive_absence_days(start: date, end: date) -> int:
    """Days covered by the certificate, counting the first and last day."""

    if end < start:
        raise ValueError("end_before_start")
    return (end - start).days + 1
