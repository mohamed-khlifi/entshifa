"""Domain errors with stable codes (RFC 7807 mapping in handlers)."""

from __future__ import annotations

from typing import Any

from ent.core.errors.codes import ErrorCode


class DomainError(Exception):
    """Base class for expected failures; never carries a display sentence."""

    code: str = ErrorCode.DOMAIN_ERROR
    http_status: int = 400

    def __init__(self, **context: Any) -> None:
        self.context: dict[str, Any] = dict(context)
        super().__init__(self.code)


class NotFoundError(DomainError):
    code = ErrorCode.NOT_FOUND
    http_status = 404


class PermissionDeniedError(DomainError):
    code = ErrorCode.FORBIDDEN
    http_status = 403


class ConflictError(DomainError):
    code = ErrorCode.CONFLICT
    http_status = 409


class ValidationError(DomainError):
    code = ErrorCode.VALIDATION_FAILED
    http_status = 422


class ClinicalSafetyError(DomainError):
    code = ErrorCode.SAFETY_BLOCK
    http_status = 409


class RecordLockedError(DomainError):
    code = ErrorCode.RECORD_SIGNED
    http_status = 409


class AuthenticationError(DomainError):
    code = ErrorCode.AUTH_UNAUTHENTICATED
    http_status = 401


class AuthInvalidCredentialsError(DomainError):
    code = ErrorCode.AUTH_INVALID_CREDENTIALS
    http_status = 401


class AuthRateLimitedError(DomainError):
    code = ErrorCode.AUTH_RATE_LIMITED
    http_status = 429


class AuthSessionRevokedError(DomainError):
    code = ErrorCode.AUTH_SESSION_REVOKED
    http_status = 401
