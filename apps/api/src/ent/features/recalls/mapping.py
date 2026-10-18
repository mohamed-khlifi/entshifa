"""Map recall rows to read models."""

from __future__ import annotations

from datetime import date
from typing import Any

from ent.features.recalls.dates import effective_status
from ent.features.recalls.models import Protocol, ProtocolRule, Recall, RecallAction
from ent.features.recalls.schemas.responses import (
    ProtocolRead,
    ProtocolRuleRead,
    RecallActionRead,
    RecallRead,
)


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


def to_protocol_rule_read(row: ProtocolRule) -> ProtocolRuleRead:
    return ProtocolRuleRead(
        public_id=row.public_id,
        sequence=int(row.sequence),
        offset_days=int(row.offset_days),
        window_days=int(row.window_days),
        action_type=row.action_type,
        action_config=(
            dict(row.action_config) if row.action_config is not None else None
        ),
        condition=dict(row.condition) if row.condition is not None else None,
        label_key=row.label_key,
    )


def to_protocol_read(row: Protocol, *, clinic_id: int) -> ProtocolRead:
    ordered_rules = sorted(
        (r for r in row.rules if r.deleted_at is None),
        key=lambda item: int(item.sequence),
    )
    return ProtocolRead(
        public_id=row.public_id,
        code=row.code,
        name_key=row.name_key,
        trigger_type=row.trigger_type,
        is_active=bool(row.is_active),
        is_clinic_override=row.clinic_id == clinic_id,
        rules=[to_protocol_rule_read(r) for r in ordered_rules],
    )
