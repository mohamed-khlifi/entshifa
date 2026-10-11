"""Map recall rows to read models."""

from __future__ import annotations

from datetime import date
from typing import Any

from ent.features.recalls.dates import effective_status
from ent.features.recalls.models import Recall, RecallAction
from ent.features.recalls.schemas.responses import RecallActionRead, RecallRead


def recall_snapshot(row: Recall) -> dict[str, Any]:
    return {
        "status": row.status,
        "due_on": row.due_on.isoformat(),
        "window_days": row.window_days,
        "attempts": row.attempts,
        "appointment_id": row.appointment_id,
        "version": row.version,
    }


def to_recall_read(
    row: Recall,
    *,
    today: date,
    source_encounter_id: str | None,
    overlap_count: int = 0,
) -> RecallRead:
    patient = row.patient
    appointment = row.appointment
    assigned = row.assigned_to
    return RecallRead(
        public_id=row.public_id,
        patient_id=patient.public_id,
        patient_display_name=f"{patient.first_name} {patient.last_name}".strip(),
        reason_text=row.reason_text,
        reason_locale=row.reason_locale,
        reason_key=row.reason_key,
        due_on=row.due_on,
        window_days=row.window_days,
        action_type=row.action_type,
        action_config=row.action_config,
        laterality=row.laterality,
        status=effective_status(
            status=row.status,
            due_on=row.due_on,
            window_days=row.window_days,
            today=today,
        ),
        appointment_id=appointment.public_id if appointment is not None else None,
        attempts=row.attempts,
        last_attempt_at=row.last_attempt_at,
        source_encounter_id=source_encounter_id,
        assigned_to_id=assigned.public_id if assigned is not None else None,
        overlap_count=overlap_count,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_action_read(row: RecallAction, *, performer_public_id: str) -> RecallActionRead:
    return RecallActionRead(
        public_id=row.public_id,
        action=row.action,
        outcome=row.outcome,
        note=row.note,
        note_locale=row.note_locale,
        performed_at=row.performed_at,
        performed_by_id=performer_public_id,
    )
