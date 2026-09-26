"""Closed value sets for patient columns (architecture §25.3 and feature spec §4.5)."""

from __future__ import annotations

SEX_VALUES = ("male", "female", "other", "unknown")

IDENTIFIER_TYPES = ("national_id", "passport", "insurance")

ALLERGY_CATEGORIES = ("drug", "food", "other")

ALLERGY_SEVERITIES = ("mild", "moderate", "severe")

MEDICATION_SOURCES = ("prescribed_here", "reported", "external")

# Architecture §25.3 examples, plus feature-spec §4.5 alerts that are flags
# rather than allergies (drug allergy stays on patient_allergy).
PATIENT_FLAG_CODES = (
    "only_hearing_ear",
    "anticoagulant",
    "ototoxic_therapy",
    "difficult_airway",
    "tracheostomy",
    "laryngeal_stenosis",
    "cochlear_implant",
    "pacemaker",
    "immunosuppressed",
    "diabetes",
    "pregnancy",
    "breastfeeding",
    "pediatric_weight_missing",
)

PROBLEM_STATUSES = ("active", "resolved", "suspected", "ruled_out")

HISTORY_CATEGORIES = (
    "ent_surgery",
    "other_surgery",
    "medical",
    "family",
    "social",
    "obstetric",
)

LATERALITY_VALUES = ("right", "left", "bilateral", "midline", "na")
