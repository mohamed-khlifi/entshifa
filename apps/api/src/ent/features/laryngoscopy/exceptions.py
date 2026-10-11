"""Laryngoscopy domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError


class LaryngoscopyNotFoundError(NotFoundError):
    code = ErrorCode.LARYNGOSCOPY_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="laryngoscopy")
            return
        super().__init__(resource="laryngoscopy", publicId=public_id)


class LaryngoscopyVersionConflictError(ConflictError):
    code = ErrorCode.LARYNGOSCOPY_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class LaryngoscopyIncompleteScoreError(ValidationError):
    code = ErrorCode.LARYNGOSCOPY_INCOMPLETE_SCORE

    def __init__(self, *, item: str | None = None, side: str | None = None) -> None:
        super().__init__(**_context(item=item, side=side))


class LaryngoscopyInvalidScoreError(ValidationError):
    code = ErrorCode.LARYNGOSCOPY_INVALID_SCORE

    def __init__(self, *, item: str | None = None, side: str | None = None) -> None:
        super().__init__(**_context(item=item, side=side))


class LaryngoscopyStructureError(ValidationError):
    code = ErrorCode.LARYNGOSCOPY_INVALID_STRUCTURE

    def __init__(self, *, body_site_code: str, reason: str) -> None:
        super().__init__(bodySiteCode=body_site_code, reason=reason)


class LaryngoscopyFindingError(ValidationError):
    code = ErrorCode.LARYNGOSCOPY_INVALID_FINDING

    def __init__(self, *, finding_code: str, status: str) -> None:
        super().__init__(findingCode=finding_code, status=status)


class LaryngoscopyExamError(ValidationError):
    code = ErrorCode.LARYNGOSCOPY_INVALID_EXAM

    def __init__(self, *, reason: str, item: str | None = None) -> None:
        context = {"reason": reason}
        if item is not None:
            context["item"] = item
        super().__init__(**context)


def _context(*, item: str | None, side: str | None) -> dict[str, str]:
    context: dict[str, str] = {}
    if item is not None:
        context["item"] = item
    if side is not None:
        context["side"] = side
    return context
