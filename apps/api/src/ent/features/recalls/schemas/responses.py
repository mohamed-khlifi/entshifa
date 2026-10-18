"""Recall read models. Integer ids never leave the process."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ent.core.schemas.base import CamelModel


class RecallActionRead(CamelModel):
    public_id: str
    action: str
    outcome: str | None
    note: str | None
    note_locale: str | None
    performed_at: datetime
    performed_by_id: str


class RecallRead(CamelModel):
    public_id: str
    patient_id: str
    patient_display_name: str
    reason_text: str | None
    reason_locale: str | None
    reason_key: str | None
    due_on: date
    window_days: int
    action_type: str
    action_config: dict[str, Any] | None
    laterality: str | None
    status: str
    appointment_id: str | None
    attempts: int
    last_attempt_at: datetime | None
    source_encounter_id: str | None
    assigned_to_id: str | None
    overlap_count: int = 0
    version: int
    created_at: datetime
    updated_at: datetime


class RecallSummaryRead(CamelModel):
    overdue: int
    upcoming: int
    unreachable: int
    active: int


class ProtocolRuleRead(CamelModel):
    public_id: str
    sequence: int
    offset_days: int
    window_days: int
    action_type: str
    action_config: dict[str, Any] | None
    condition: dict[str, Any] | None
    label_key: str


class ProtocolRead(CamelModel):
    public_id: str
    code: str
    name_key: str
    trigger_type: str
    is_active: bool
    is_clinic_override: bool
    rules: list[ProtocolRuleRead]
