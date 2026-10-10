"""Closed values for prescription columns (architecture section 25.11, P2-08)."""

from __future__ import annotations

DRUG_FORMS = ("tablet", "syrup", "spray", "drops", "injection")

# Feature spec section 14.2 routes.
ROUTES = ("oral", "nasal", "otic", "topical", "injection")

PRESCRIPTION_STATUSES = ("draft", "issued", "cancelled")

# Closed vocabulary for drug.pregnancy_category. Null means unknown, not safe.
PREGNANCY_CATEGORIES = ("caution", "contraindicated", "compatible")

# ICD-10 blocks seeded in ent.seeds.icd10_ent (H90 conductive/sensorineural/mixed,
# H91 other hearing loss including ototoxic, presbycusis, sudden, unspecified).
HEARING_LOSS_CODE_PREFIXES = ("H90", "H91")

OVERRIDABLE_ALERTS = (
    "prescription.allergy_conflict",
    "prescription.dose_above_maximum",
)

SAFETY_CONTEXT_LIMIT = 500
