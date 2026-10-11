"""Otology domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError


class OtologyNotFoundError(NotFoundError):
    code = ErrorCode.OTOLOGY_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="otology_exam")
            return
        super().__init__(resource="otology_exam", publicId=public_id)


class EarDeviceNotFoundError(NotFoundError):
    code = ErrorCode.OTOLOGY_DEVICE_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="ear_device")
            return
        super().__init__(resource="ear_device", publicId=public_id)


class OtologyVersionConflictError(ConflictError):
    code = ErrorCode.OTOLOGY_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class OtologyInvalidExamError(ValidationError):
    code = ErrorCode.OTOLOGY_INVALID_EXAM

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason=reason)


class OtologyStructureError(ValidationError):
    code = ErrorCode.OTOLOGY_INVALID_STRUCTURE

    def __init__(self, *, body_site_code: str, reason: str) -> None:
        super().__init__(bodySiteCode=body_site_code, reason=reason)


class OtologyFindingError(ValidationError):
    code = ErrorCode.OTOLOGY_INVALID_FINDING

    def __init__(self, *, finding_code: str, status: str) -> None:
        super().__init__(findingCode=finding_code, status=status)
