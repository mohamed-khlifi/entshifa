"""Scheduling response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ent.core.schemas.base import CamelModel


class AppointmentTypeRead(CamelModel):
    public_id: str
    code: str
    name_key: str
    default_duration_min: int
    color: str
    requires_room: bool
    version: int
    created_at: datetime
    updated_at: datetime


class AppointmentOverlapWarning(CamelModel):
    code: str = "appointment.doctor_overlap"
    overlapping_appointment_ids: list[str] = Field(default_factory=list)


class QuestionnaireStatusRead(CamelModel):
    """Stub until phase 5 instruments are wired."""

    status: str = "not_applicable"


class AppointmentRead(CamelModel):
    public_id: str
    site_id: str
    patient_id: str
    user_id: str
    appointment_type_id: str
    starts_at: datetime
    ends_at: datetime
    status: str
    reason_text: str | None
    room: str | None
    arrived_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    cancellation_reason: str | None
    questionnaire_status: QuestionnaireStatusRead
    overlap_warnings: list[AppointmentOverlapWarning] = Field(default_factory=list)
    version: int
    created_at: datetime
    updated_at: datetime


class WaitingRoomEntryRead(CamelModel):
    appointment: AppointmentRead
    patient_display_name: str
    doctor_display_name: str


class SchedulableDoctorRead(CamelModel):
    public_id: str
    first_name: str
    last_name: str
