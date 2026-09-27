"""Scheduling domain errors."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import DomainError, ValidationError


class AppointmentInvalidTransitionError(DomainError):
    code = ErrorCode.APPOINTMENT_INVALID_TRANSITION
    http_status = 422

    def __init__(self, *, from_status: str, to_status: str) -> None:
        super().__init__(fromStatus=from_status, toStatus=to_status)


class AppointmentInvalidTimeRangeError(ValidationError):
    code = ErrorCode.APPOINTMENT_INVALID_TIME_RANGE
