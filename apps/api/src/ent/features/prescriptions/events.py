"""Prescription domain events (past tense)."""

from __future__ import annotations

from ent.core.events.events import DomainEvent

PRESCRIPTION_DRAFTED = "prescription.drafted"
PRESCRIPTION_ISSUED = "prescription.issued"
PRESCRIPTION_CANCELLED = "prescription.cancelled"


def prescription_event(
    name: str,
    *,
    prescription_public_id: str,
    clinic_id: int,
    patient_public_id: str,
) -> DomainEvent:
    return DomainEvent(
        name=name,
        payload={
            "prescription_public_id": prescription_public_id,
            "clinic_id": clinic_id,
            "patient_public_id": patient_public_id,
        },
    )
