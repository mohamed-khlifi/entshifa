"""Patient domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError


class PatientPossibleDuplicateError(ConflictError):
    code = ErrorCode.PATIENT_POSSIBLE_DUPLICATE


class PatientMrnConflictError(ConflictError):
    code = ErrorCode.PATIENT_MRN_CONFLICT


class PatientVersionConflictError(ConflictError):
    code = ErrorCode.PATIENT_VERSION_CONFLICT


class PatientIdempotencyMismatchError(ConflictError):
    code = ErrorCode.PATIENT_IDEMPOTENCY_MISMATCH


class PatientMergeInvalidError(ConflictError):
    code = ErrorCode.PATIENT_MERGE_INVALID
