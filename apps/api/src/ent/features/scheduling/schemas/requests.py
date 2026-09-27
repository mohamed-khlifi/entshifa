"""Scheduling request schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ent.core.schemas.base import CamelModel


class AppointmentTypeCreate(CamelModel):
    code: str = Field(min_length=1, max_length=40)
    name_key: str = Field(min_length=1, max_length=80)
    default_duration_min: int = Field(ge=5, le=480)
    color: str = Field(min_length=4, max_length=12)
    requires_room: bool = False


class AppointmentTypeUpdate(CamelModel):
    name_key: str | None = Field(default=None, min_length=1, max_length=80)
    default_duration_min: int | None = Field(default=None, ge=5, le=480)
    color: str | None = Field(default=None, min_length=4, max_length=12)
    requires_room: bool | None = None
    version: int = Field(ge=1)


class AppointmentCreate(CamelModel):
    site_id: str
    patient_id: str
    user_id: str
    appointment_type_id: str
    starts_at: datetime
    ends_at: datetime | None = None
    room: str | None = Field(default=None, max_length=40)
    reason_text: str | None = Field(default=None, max_length=255)


class AppointmentUpdate(CamelModel):
    site_id: str | None = None
    user_id: str | None = None
    appointment_type_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    room: str | None = Field(default=None, max_length=40)
    reason_text: str | None = Field(default=None, max_length=255)
    version: int = Field(ge=1)


class AppointmentCancel(CamelModel):
    cancellation_reason: str = Field(min_length=1, max_length=160)
