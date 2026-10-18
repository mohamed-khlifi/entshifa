"""Closed values for manual recalls (architecture §25.15, feature spec §15.3)."""

from __future__ import annotations

RECALL_SOURCE_TYPES = ("manual", "procedure")

PROTOCOL_TRIGGER_TYPES = ("procedure", "diagnosis", "finding", "surgery", "manual")

RECALL_ACTION_TYPES = ("visit", "test", "call", "questionnaire", "document")

RECALL_STATUSES = (
    "pending",
    "booked",
    "done",
    "overdue",
    "cancelled",
    "unreachable",
)

RECALL_CONTACT_ACTIONS = ("sms", "call", "email", "whatsapp", "booked")

RECALL_OUTCOMES = (
    "reached",
    "no_answer",
    "voicemail",
    "unreachable",
    "confirmed",
    "declined",
)

RECALL_LATERALITIES = ("right", "left", "bilateral", "midline", "na")

RECALL_TESTS = ("audiogram", "tympanometry", "endoscopy", "imaging")

# Assistant work-list horizon. Not a surveillance interval.
UPCOMING_HORIZON_DAYS = 28

OPEN_STATUSES = frozenset({"pending", "booked", "unreachable"})

MUTABLE_STATUSES = frozenset({"pending", "booked", "unreachable"})
