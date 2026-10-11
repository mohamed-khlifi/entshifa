"""Shared procedure-record values. Child exams reuse these; they do not repeat them."""

from __future__ import annotations

from typing import Literal

PROCEDURE_STATUSES = ("draft", "signed", "amended")
LOCKED_STATUSES = frozenset({"signed", "amended"})
PROCEDURE_SETTINGS = ("office", "ot")
ANESTHESIA_TYPES = ("none", "topical_spray", "local_infiltration", "general")
TOLERANCE_VALUES = (
    "well_tolerated",
    "mild_discomfort",
    "moderate_discomfort",
    "poorly_tolerated",
    "aborted",
)
COMPLICATION_KINDS = frozenset({"finding", "diagnosis"})

ProcedureStatus = Literal["draft", "signed", "amended"]
ProcedureSetting = Literal["office", "ot"]
AnesthesiaType = Literal["none", "topical_spray", "local_infiltration", "general"]
ToleranceValue = Literal[
    "well_tolerated",
    "mild_discomfort",
    "moderate_discomfort",
    "poorly_tolerated",
    "aborted",
]
