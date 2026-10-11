"""Document domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ClinicalSafetyError, ValidationError


class DocumentEncounterRequiredError(ValidationError):
    code = ErrorCode.DOCUMENTS_ENCOUNTER_REQUIRED


class DocumentPayloadError(ValidationError):
    code = ErrorCode.DOCUMENTS_PAYLOAD_INVALID


class DocumentAbsenceRangeError(ValidationError):
    code = ErrorCode.DOCUMENTS_ABSENCE_RANGE


class ImagingMriBlockedError(ClinicalSafetyError):
    """MRI was requested for a patient with a non-MRI-safe implant."""

    code = ErrorCode.DOCUMENTS_MRI_IMPLANT_BLOCKED

    def __init__(self, *, flags: tuple[str, ...]) -> None:
        super().__init__(flags=list(flags))
