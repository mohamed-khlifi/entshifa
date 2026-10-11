"""Endoscopy domain errors. Codes are stable; the UI translates them."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError


class EndoscopyNotFoundError(NotFoundError):
    code = ErrorCode.ENDOSCOPY_NOT_FOUND

    def __init__(self, *, public_id: str | None = None) -> None:
        if public_id is None:
            super().__init__(resource="endoscopy")
            return
        super().__init__(resource="endoscopy", publicId=public_id)


class EndoscopyVersionConflictError(ConflictError):
    code = ErrorCode.ENDOSCOPY_VERSION_CONFLICT

    def __init__(self, *, server_version: int, client_version: int) -> None:
        super().__init__(serverVersion=server_version, clientVersion=client_version)


class EndoscopyIncompleteScoreError(ValidationError):
    code = ErrorCode.ENDOSCOPY_INCOMPLETE_SCORE

    def __init__(
        self,
        *,
        item: str | None = None,
        side: str | None = None,
    ) -> None:
        super().__init__(**_score_context(item=item, side=side))


class EndoscopyInvalidScoreError(ValidationError):
    code = ErrorCode.ENDOSCOPY_INVALID_SCORE

    def __init__(
        self,
        *,
        item: str | None = None,
        side: str | None = None,
    ) -> None:
        super().__init__(**_score_context(item=item, side=side))


class EndoscopyStructureError(ValidationError):
    code = ErrorCode.ENDOSCOPY_INVALID_STRUCTURE

    def __init__(self, *, body_site_code: str, reason: str) -> None:
        super().__init__(bodySiteCode=body_site_code, reason=reason)


class EndoscopyFindingError(ValidationError):
    code = ErrorCode.ENDOSCOPY_INVALID_FINDING

    def __init__(self, *, finding_code: str, status: str) -> None:
        super().__init__(findingCode=finding_code, status=status)


def _score_context(
    *,
    item: str | None,
    side: str | None,
) -> dict[str, str]:
    context: dict[str, str] = {}
    if item is not None:
        context["item"] = item
    if side is not None:
        context["side"] = side
    return context
