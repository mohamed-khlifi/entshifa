"""Domain error types and codes."""

from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import (
    AuthenticationError,
    AuthInvalidCredentialsError,
    AuthRateLimitedError,
    AuthSessionRevokedError,
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
    "ErrorCode",
    "NotFoundError",
    "PermissionDeniedError",
    "RecordLockedError",
    "ValidationError",
]
