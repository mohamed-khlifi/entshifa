"""Audiology domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, RecordLockedError


class AudiogramNotFoundError(NotFoundError):
    code = ErrorCode.AUDIOLOGY_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="audiogram")
            return
        super().__init__(resource="audiogram", publicId=public_id)


class AudiogramVersionConflictError(ConflictError):
    code = ErrorCode.AUDIOLOGY_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class AudiogramLockedError(RecordLockedError):
    code = ErrorCode.AUDIOLOGY_ALREADY_FINALIZED

    def __init__(self, *, public_id: str | None = None) -> None:
        context: dict[str, str] = {}
        if public_id is not None:
            context["publicId"] = public_id
        super().__init__(**context)


class AudiogramInvalidThresholdError(ConflictError):
    code = ErrorCode.AUDIOLOGY_INVALID_THRESHOLD
    http_status = 422


class AudiogramDuplicateThresholdError(ConflictError):
    code = ErrorCode.AUDIOLOGY_DUPLICATE_THRESHOLD
    http_status = 422


class AudiogramIncompleteThresholdsError(ConflictError):
    code = ErrorCode.AUDIOLOGY_INCOMPLETE_THRESHOLDS
    http_status = 422


class AudiogramIdempotencyMismatchError(ConflictError):
    code = ErrorCode.AUDIOLOGY_IDEMPOTENCY_MISMATCH
