"""Procedure domain events (past tense)."""

from __future__ import annotations

from datetime import datetime

from ent.core.events.events import DomainEvent

PROCEDURE_PERFORMED = "procedure.performed"


def procedure_performed_event(
    *,
    clinic_id: int,
    procedure_public_id: str,
    patient_public_id: str,
    encounter_public_id: str | None,
    procedure_concept_code: str,
    performed_at: datetime,
    performed_by_public_id: str,
    laterality: str,
    setting: str,
    anesthesia: str,
    has_complications: bool,
) -> DomainEvent:
    """Emitted when a procedure is signed. Recall protocols listen in P3-08."""

    return DomainEvent(
        name=PROCEDURE_PERFORMED,
        payload={
            "clinic_id": clinic_id,
            "procedure_public_id": procedure_public_id,
            "patient_public_id": patient_public_id,
            "encounter_public_id": encounter_public_id,
            "procedure_concept_code": procedure_concept_code,
            "performed_at": performed_at.isoformat(),
            "performed_by_public_id": performed_by_public_id,
            "laterality": laterality,
            "setting": setting,
            "anesthesia": anesthesia,
            "has_complications": has_complications,
        },
    )
