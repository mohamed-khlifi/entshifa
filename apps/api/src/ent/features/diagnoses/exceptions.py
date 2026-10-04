"""Diagnosis domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import NotFoundError, ValidationError


class DiagnosisNotFoundError(NotFoundError):
    code = ErrorCode.DIAGNOSIS_NOT_FOUND


class DiagnosisInvalidConceptError(ValidationError):
    code = ErrorCode.DIAGNOSIS_INVALID_CONCEPT
