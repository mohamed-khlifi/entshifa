"""Patient domain events (past tense)."""

from __future__ import annotations

from ent.core.events.events import DomainEvent

PATIENT_CREATED = "patient.created"
PATIENT_MERGED = "patient.merged"


def patient_created_event(
    *,
    patient_public_id: str,
    clinic_id: int,
) -> DomainEvent:
    return DomainEvent(
        name=PATIENT_CREATED,
        payload={
            "patient_public_id": patient_public_id,
            "clinic_id": clinic_id,
        },
    )


def patient_merged_event(
    *,
    surviving_public_id: str,
    merged_public_id: str,
    clinic_id: int,
) -> DomainEvent:
    return DomainEvent(
        name=PATIENT_MERGED,
        payload={
            "surviving_public_id": surviving_public_id,
            "merged_public_id": merged_public_id,
            "clinic_id": clinic_id,
        },
    )
