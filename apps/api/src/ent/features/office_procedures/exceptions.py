"""Office-procedure errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError


class OfficeProcedureNotFoundError(NotFoundError):
    code = ErrorCode.OFFICE_PROCEDURE_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="office_procedure")
            return
        super().__init__(resource="office_procedure", publicId=public_id)


class OfficeProcedureVersionConflictError(ConflictError):
    code = ErrorCode.OFFICE_PROCEDURE_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class OfficeProcedureInvalidError(ValidationError):
    code = ErrorCode.OFFICE_PROCEDURE_INVALID

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason=reason)
