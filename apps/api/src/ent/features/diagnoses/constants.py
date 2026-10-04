"""Closed values for encounter diagnoses (architecture §25.11, feature spec §5.6)."""

from __future__ import annotations

DIAGNOSIS_STATUSES = ("suspected", "confirmed", "ruled_out")

DIAGNOSIS_SOURCES = ("clinician", "copy_forward")

DIAGNOSIS_LATERALITIES = ("right", "left", "bilateral", "midline", "na")
