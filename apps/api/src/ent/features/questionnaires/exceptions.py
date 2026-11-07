"""Questionnaire domain errors."""

from __future__ import annotations

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)


class InstrumentNotFoundError(NotFoundError):
    code = ErrorCode.QUESTIONNAIRE_INSTRUMENT_NOT_FOUND


class InstrumentCodeConflictError(ConflictError):
    code = ErrorCode.QUESTIONNAIRE_CODE_CONFLICT


class InstrumentVersionConflictError(ConflictError):
    code = ErrorCode.QUESTIONNAIRE_VERSION_CONFLICT


class InstrumentSystemImmutableError(ConflictError):
    code = ErrorCode.QUESTIONNAIRE_SYSTEM_IMMUTABLE


class InstrumentTranslationIncompleteError(ValidationError):
    code = ErrorCode.QUESTIONNAIRE_TRANSLATION_INCOMPLETE


class InstrumentInvalidDefinitionError(ValidationError):
    code = ErrorCode.QUESTIONNAIRE_INVALID_DEFINITION


class InstrumentIncompleteResponseError(ValidationError):
    code = ErrorCode.QUESTIONNAIRE_INCOMPLETE_RESPONSE

    def __init__(self, *, missing_item_codes: tuple[str, ...]) -> None:
        super().__init__(missingItems=",".join(missing_item_codes))


class InstrumentInvalidAnswerError(ValidationError):
    code = ErrorCode.QUESTIONNAIRE_INVALID_ANSWER

    def __init__(self, *, item_code: str, value: int) -> None:
        super().__init__(itemCode=item_code, value=value)


class QuestionnaireInvitationNotFoundError(NotFoundError):
    code = ErrorCode.QUESTIONNAIRE_INVITATION_NOT_FOUND


class QuestionnaireInvitationExpiredError(ValidationError):
    code = ErrorCode.QUESTIONNAIRE_INVITATION_EXPIRED
    http_status = 410


class QuestionnaireInvitationAlreadyCompletedError(ConflictError):
    code = ErrorCode.QUESTIONNAIRE_INVITATION_ALREADY_COMPLETED


class QuestionnaireRateLimitedError(DomainError):
    code = ErrorCode.QUESTIONNAIRE_RATE_LIMITED
    http_status = 429


class QuestionnaireContactMissingError(ValidationError):
    code = ErrorCode.QUESTIONNAIRE_CONTACT_MISSING


class QuestionnaireResponseNotFoundError(NotFoundError):
    code = ErrorCode.QUESTIONNAIRE_RESPONSE_NOT_FOUND


class QuestionnaireIdempotencyMismatchError(ConflictError):
    code = ErrorCode.QUESTIONNAIRE_IDEMPOTENCY_MISMATCH
