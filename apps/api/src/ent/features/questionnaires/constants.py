"""Closed values for questionnaire instruments (architecture §25.10)."""

from __future__ import annotations

INSTRUMENT_CATEGORIES = (
    "sinonasal",
    "ear",
    "vertigo",
    "voice",
    "reflux",
    "swallowing",
    "sleep",
    "qol",
    "head_neck",
    "airway",
    "pediatrics",
    "other",
)

INSTRUMENT_RESPONDENTS = ("patient", "clinician", "parent")

INSTRUMENT_SCORING_TYPES = ("sum", "weighted_sum", "custom")

INSTRUMENT_LOCALES = ("en", "fr", "ar")
