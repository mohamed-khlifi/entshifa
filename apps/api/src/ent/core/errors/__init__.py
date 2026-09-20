"""Domain error types."""

from ent.core.errors.exceptions import (
    AuthInvalidCredentialsError,
    AuthRateLimitedError,
    AuthSessionRevokedError,
    AuthenticationError,
    ClinicalSafetyError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    RecordLockedError,
    ValidationError,
)

__all__ = [
    "AuthInvalidCredentialsError",
    "AuthRateLimitedError",
    "AuthSessionRevokedError",
    "AuthenticationError",
    "ClinicalSafetyError",
    "ConflictError",
    "DomainError",
    "NotFoundError",
    "PermissionDeniedError",
    "RecordLockedError",
    "ValidationError",
]
