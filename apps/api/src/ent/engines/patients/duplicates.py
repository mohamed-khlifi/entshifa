"""Duplicate detection for patient registration.

A likely duplicate is the same folded name plus birth date, or the same
normalized phone. The service prompts; it does not silently create.
"""

from __future__ import annotations

from datetime import date

VERSION = "1.0.0"
REFERENCE = (
    "EntShifa feature specification section 4.1: same name plus date of birth, "
    "or the same phone, is a possible existing patient."
)


def is_likely_duplicate(
    *,
    left_name_normalized: str,
    left_birth_date: date,
    left_phones: tuple[str | None, ...],
    right_name_normalized: str,
    right_birth_date: date,
    right_phones: tuple[str | None, ...],
) -> bool:
    """Return whether two identity snapshots should raise a duplicate prompt."""

    if (
        left_name_normalized
        and left_name_normalized == right_name_normalized
        and left_birth_date == right_birth_date
    ):
        return True

    left = {phone for phone in left_phones if phone}
    right = {phone for phone in right_phones if phone}
    return bool(left and right and left.intersection(right))
