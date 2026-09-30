"""Observation domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError


class ObservationNotFoundError(NotFoundError):
    code = ErrorCode.OBSERVATION_NOT_FOUND


class ObservationInvalidValueError(ValidationError):
    code = ErrorCode.OBSERVATION_INVALID_VALUE


class ObservationVersionConflictError(ConflictError):
    code = ErrorCode.OBSERVATION_VERSION_CONFLICT
