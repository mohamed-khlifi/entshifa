"""Audiology domain events (past tense)."""

from __future__ import annotations

from ent.core.events.events import DomainEvent

AUDIOGRAM_CREATED = "audiogram.created"
AUDIOGRAM_BASELINE_CHANGED = "audiogram.baseline_changed"
_CREATE_RESOURCE = "audiogram.create"


def audiogram_created_event(
    *,
    clinic_id: int,
    audiogram_public_id: str,
    patient_public_id: str,
    encounter_public_id: str | None,
) -> DomainEvent:
    return DomainEvent(
        name=AUDIOGRAM_CREATED,
        payload={
            "clinic_id": clinic_id,
            "audiogram_public_id": audiogram_public_id,
            "patient_public_id": patient_public_id,
            "encounter_public_id": encounter_public_id,
        },
    )


def audiogram_baseline_changed_event(
    *,
    clinic_id: int,
    audiogram_public_id: str,
    patient_public_id: str,
    is_baseline: bool,
) -> DomainEvent:
    return DomainEvent(
        name=AUDIOGRAM_BASELINE_CHANGED,
        payload={
            "clinic_id": clinic_id,
            "audiogram_public_id": audiogram_public_id,
            "patient_public_id": patient_public_id,
            "is_baseline": is_baseline,
        },
    )
