"""Recall domain events (past tense)."""

from __future__ import annotations

from ent.core.events.events import DomainEvent

RECALL_CREATED = "recall.created"
RECALL_BOOKED = "recall.booked"
RECALL_COMPLETED = "recall.completed"


def recall_created_event(
    *,
    recall_public_id: str,
    patient_public_id: str,
    clinic_id: int,
) -> DomainEvent:
    return DomainEvent(
        name=RECALL_CREATED,
        payload={
            "recall_public_id": recall_public_id,
            "patient_public_id": patient_public_id,
            "clinic_id": clinic_id,
        },
    )
