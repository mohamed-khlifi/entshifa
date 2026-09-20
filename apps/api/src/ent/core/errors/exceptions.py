"""Domain errors with stable codes (RFC 7807 mapping in handlers)."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected failures."""

    code: str = "domain.error"
    http_status: int = 400

    def __init__(self, **context: object) -> None:
        self.context = context
        super().__init__(self.code)


class NotFoundError(DomainError):
    code = "not_found"
    http_status = 404


class PermissionDeniedError(DomainError):
    code = "forbidden"
    http_status = 403


class ConflictError(DomainError):
    code = "conflict"
    http_status = 409


class ValidationError(DomainError):
    code = "validation_failed"
    http_status = 422


class ClinicalSafetyError(DomainError):
    code = "safety_block"
    http_status = 409


class RecordLockedError(DomainError):
    code = "record_signed"
    http_status = 409


class AuthenticationError(DomainError):
    code = "auth.unauthenticated"
    http_status = 401


class AuthInvalidCredentialsError(DomainError):
    code = "auth.invalid_credentials"
    http_status = 401


class AuthRateLimitedError(DomainError):
    code = "auth.rate_limited"
    http_status = 429


class AuthSessionRevokedError(DomainError):
    code = "auth.session_revoked"
    http_status = 401
