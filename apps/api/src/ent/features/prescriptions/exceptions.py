"""Prescription domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from typing import Any

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import (
    ClinicalSafetyError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class PrescriptionNotFoundError(NotFoundError):
    code = ErrorCode.PRESCRIPTION_NOT_FOUND


class FormularyEntryNotFoundError(NotFoundError):
    code = ErrorCode.PRESCRIPTION_FORMULARY_NOT_FOUND


class PrescriptionInvalidStatusError(ConflictError):
    code = ErrorCode.PRESCRIPTION_INVALID_STATUS

    def __init__(self, *, status: str) -> None:
        super().__init__(status=status)


class PrescriptionVersionConflictError(ConflictError):
    code = ErrorCode.PRESCRIPTION_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class PrescriptionIdempotencyMismatchError(ConflictError):
    code = ErrorCode.PRESCRIPTION_IDEMPOTENCY_MISMATCH


class PrescriptionDosingRuleError(ValidationError):
    code = ErrorCode.PRESCRIPTION_DOSING_RULE_INVALID


class PrescriptionDosingInputError(ValidationError):
    code = ErrorCode.PRESCRIPTION_DOSING_INPUT_INVALID

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason=reason)


class PrescriptionBlockedError(ClinicalSafetyError):
    """One or more safety blocks were not overridden."""

    def __init__(self, alerts: list[dict[str, Any]]) -> None:
        codes = {str(alert["code"]) for alert in alerts}
        if codes == {ErrorCode.PRESCRIPTION_ALLERGY_CONFLICT}:
            self.code = ErrorCode.PRESCRIPTION_ALLERGY_CONFLICT
        elif codes == {ErrorCode.PRESCRIPTION_PEDIATRIC_WEIGHT_MISSING}:
            self.code = ErrorCode.PRESCRIPTION_PEDIATRIC_WEIGHT_MISSING
        elif codes == {ErrorCode.PRESCRIPTION_DOSE_ABOVE_MAXIMUM}:
            self.code = ErrorCode.PRESCRIPTION_DOSE_ABOVE_MAXIMUM
        else:
            self.code = ErrorCode.PRESCRIPTION_SAFETY_BLOCKED
        super().__init__(alerts=alerts)
