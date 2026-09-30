"""Closed value sets for encounter columns (architecture §25.5)."""

from __future__ import annotations

ENCOUNTER_TYPES = (
    "consultation",
    "follow_up",
    "procedure",
    "post_op",
    "result_review",
    "teleconsultation",
)

ENCOUNTER_STATUSES = ("draft", "signed", "amended", "cancelled")

LOCKED_STATUSES = frozenset({"signed", "amended", "cancelled"})
