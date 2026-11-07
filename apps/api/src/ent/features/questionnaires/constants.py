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

QUESTIONNAIRE_CHANNELS = ("sms", "whatsapp", "email", "tablet")

QUESTIONNAIRE_CONTEXTS = (
    "pre_visit",
    "waiting_room",
    "post_op_3m",
    "post_op_6m",
    "post_op_12m",
    "follow_up",
)

QUESTIONNAIRE_ENTERED_BY = ("patient", "staff", "clinician")

QUESTIONNAIRE_TABLET_TTL_MINUTES = 240
QUESTIONNAIRE_REMOTE_TTL_MINUTES = 4320
QUESTIONNAIRE_EXPIRES_MIN_BOUND = 15
QUESTIONNAIRE_EXPIRES_MAX_BOUND = 10080
