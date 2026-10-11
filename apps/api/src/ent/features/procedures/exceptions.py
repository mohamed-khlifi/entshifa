"""Procedure domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, RecordLockedError


class ProcedureRecordNotFoundError(NotFoundError):
    code = ErrorCode.PROCEDURE_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="procedure")
            return
        super().__init__(resource="procedure", publicId=public_id)


class ProcedureVersionConflictError(ConflictError):
    code = ErrorCode.PROCEDURE_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class ProcedureInvalidTransitionError(ConflictError):
    code = ErrorCode.PROCEDURE_INVALID_TRANSITION
    http_status = 422

    def __init__(self, *, from_status: str, to_status: str) -> None:
        super().__init__(fromStatus=from_status, toStatus=to_status)


class ProcedureLockedError(RecordLockedError):
    code = ErrorCode.PROCEDURE_ALREADY_SIGNED

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


class ProcedureConceptInvalidError(ConflictError):
    code = ErrorCode.PROCEDURE_INVALID_CONCEPT
    http_status = 422

    def __init__(self, *, concept_public_id: str, kind: str, role: str) -> None:
        super().__init__(conceptId=concept_public_id, kind=kind, role=role)
