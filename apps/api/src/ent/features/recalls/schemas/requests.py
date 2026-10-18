"""Recall request schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel

RecallActionType = Literal["visit", "test", "call", "questionnaire", "document"]
RecallContactAction = Literal["sms", "call", "email", "whatsapp", "booked"]
RecallOutcome = Literal[
    "reached",
    "no_answer",
    "voicemail",
    "unreachable",
    "confirmed",
    "declined",
]
RecallLaterality = Literal["right", "left", "bilateral", "midline", "na"]
RecallTest = Literal["audiogram", "tympanometry", "endoscopy", "imaging"]
RecallBucket = Literal["overdue", "upcoming", "unreachable", "active"]


class RecallActionConfig(CamelModel):
    test: RecallTest | None = None
    instrument: str | None = Field(default=None, max_length=40, pattern=r"^[a-z0-9_]+$")


class RecallAppointmentCreate(CamelModel):
    site_id: str
    user_id: str
    appointment_type_id: str
    starts_at: datetime
    ends_at: datetime | None = None
    room: str | None = Field(default=None, max_length=40)


class RecallCreate(CamelModel):
    patient_id: str
    reason_text: str = Field(min_length=1, max_length=255)
    reason_locale: str = Field(min_length=2, max_length=10)
    due_on: date | None = None
    interval_days: int | None = Field(default=None, ge=1, le=3650)
    window_days: int = Field(default=14, ge=0, le=180)
    action_type: RecallActionType
    action_config: RecallActionConfig | None = None
    laterality: RecallLaterality | None = None
    source_encounter_id: str | None = None
    assigned_to_id: str | None = None
    appointment: RecallAppointmentCreate | None = None


class RecallActionCreate(CamelModel):
    action: RecallContactAction
    outcome: RecallOutcome | None = None
    note: str | None = Field(default=None, max_length=255)
    note_locale: str | None = Field(default=None, min_length=2, max_length=10)
    version: int = Field(ge=1)


class RecallBook(CamelModel):
    appointment: RecallAppointmentCreate
    version: int = Field(ge=1)


class RecallCancel(CamelModel):
    reason: str = Field(min_length=1, max_length=200)
    version: int = Field(ge=1)


class RecallComplete(CamelModel):
    version: int = Field(ge=1)
    completed_encounter_id: str | None = None


class RecallUpdate(CamelModel):
    due_on: date | None = None
    window_days: int | None = Field(default=None, ge=0, le=180)
    reason_text: str | None = Field(default=None, min_length=1, max_length=255)
    reason_locale: str | None = Field(default=None, min_length=2, max_length=10)
    assigned_to_id: str | None = None
    version: int = Field(ge=1)


class ProtocolRuleUpdate(CamelModel):
    sequence: int = Field(ge=1, le=50)
    offset_days: int = Field(ge=0, le=3650)
    window_days: int = Field(ge=0, le=180)
    offset_months: int | None = Field(default=None, ge=1, le=120)
    repeat_every_months: int | None = Field(default=None, ge=1, le=120)
    repeat_every_days: int | None = Field(default=None, ge=1, le=3650)


class ProtocolUpdate(CamelModel):
    is_active: bool | None = None
    rules: list[ProtocolRuleUpdate] = Field(default_factory=list, max_length=50)
