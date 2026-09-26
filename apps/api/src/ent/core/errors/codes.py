"""Stable, namespaced machine-readable error codes."""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    """Codes returned in problem+json; the frontend translates by code."""

    DOMAIN_ERROR = "domain.error"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    VALIDATION_FAILED = "validation_failed"
    SAFETY_BLOCK = "safety_block"
    RECORD_SIGNED = "record_signed"
    INTERNAL_ERROR = "internal_error"

    AUTH_UNAUTHENTICATED = "auth.unauthenticated"
    AUTH_INVALID_CREDENTIALS = "auth.invalid_credentials"
    AUTH_RATE_LIMITED = "auth.rate_limited"
    AUTH_SESSION_REVOKED = "auth.session_revoked"
    AUTH_MFA_INVALID = "auth.mfa_invalid"

    PATIENT_POSSIBLE_DUPLICATE = "patient.possible_duplicate"
    PATIENT_MRN_CONFLICT = "patient.mrn_conflict"
    PATIENT_VERSION_CONFLICT = "patient.version_conflict"
    PATIENT_IDEMPOTENCY_MISMATCH = "patient.idempotency_mismatch"
    PATIENT_MERGE_INVALID = "patient.merge_invalid"
