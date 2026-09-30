"""Encounter domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, RecordLockedError


class EncounterNotFoundError(NotFoundError):
    code = ErrorCode.ENCOUNTER_NOT_FOUND


class EncounterVersionConflictError(ConflictError):
    code = ErrorCode.ENCOUNTER_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class EncounterInvalidTransitionError(ConflictError):
    code = ErrorCode.ENCOUNTER_INVALID_TRANSITION
    http_status = 422

    def __init__(self, *, from_status: str, to_status: str) -> None:
        super().__init__(fromStatus=from_status, toStatus=to_status)


class EncounterLockedError(RecordLockedError):
    code = ErrorCode.ENCOUNTER_ALREADY_SIGNED

    def __init__(
        self,
        *,
        public_id: str | None = None,
        status: str | None = None,
    ) -> None:
        context: dict[str, str] = {}
        if public_id is not None:
            context["publicId"] = public_id
        if status is not None:
            context["status"] = status
        super().__init__(**context)
