"""Recall domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError


class RecallNotFoundError(NotFoundError):
    code = ErrorCode.RECALL_NOT_FOUND


class RecallVersionConflictError(ConflictError):
    code = ErrorCode.RECALL_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class RecallInvalidStatusError(ConflictError):
    code = ErrorCode.RECALL_INVALID_STATUS

    def __init__(self, *, status: str) -> None:
        super().__init__(status=status)


class RecallIdempotencyMismatchError(ConflictError):
    code = ErrorCode.RECALL_IDEMPOTENCY_MISMATCH


class RecallDueRequiredError(ValidationError):
    code = ErrorCode.RECALL_DUE_REQUIRED
