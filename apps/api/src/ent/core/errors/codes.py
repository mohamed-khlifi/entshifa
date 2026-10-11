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

    APPOINTMENT_INVALID_TRANSITION = "appointment.invalid_transition"
    APPOINTMENT_INVALID_TIME_RANGE = "appointment.invalid_time_range"

    DOCUMENTS_UNDECLARED_PLACEHOLDER = "documents.undeclared_placeholder"
    DOCUMENTS_TEMPLATE_SYNTAX = "documents.template_syntax"
    DOCUMENTS_IMMUTABLE = "documents.immutable"
    DOCUMENTS_NOT_RENDERED = "documents.not_rendered"
    DOCUMENTS_ENCOUNTER_REQUIRED = "documents.encounter_required"
    DOCUMENTS_PAYLOAD_INVALID = "documents.payload_invalid"
    DOCUMENTS_ABSENCE_RANGE = "documents.absence_range"
    DOCUMENTS_MRI_IMPLANT_BLOCKED = "documents.mri_implant_blocked"

    OBSERVATION_NOT_FOUND = "observation.not_found"
    OBSERVATION_INVALID_VALUE = "observation.invalid_value_type"
    OBSERVATION_VERSION_CONFLICT = "observation.version_conflict"

    ENCOUNTER_NOT_FOUND = "encounter.not_found"
    ENCOUNTER_VERSION_CONFLICT = "encounter.version_conflict"
    ENCOUNTER_INVALID_TRANSITION = "encounter.invalid_transition"
    ENCOUNTER_ALREADY_SIGNED = "encounter.already_signed"
    ENCOUNTER_TEMPLATE_NOT_FOUND = "encounter.template_not_found"

    DIAGNOSIS_NOT_FOUND = "diagnosis.not_found"
    DIAGNOSIS_INVALID_CONCEPT = "diagnosis.invalid_concept"

    PRESCRIPTION_NOT_FOUND = "prescription.not_found"
    PRESCRIPTION_FORMULARY_NOT_FOUND = "prescription.formulary_not_found"
    PRESCRIPTION_INVALID_STATUS = "prescription.invalid_status"
    PRESCRIPTION_VERSION_CONFLICT = "prescription.version_conflict"
    PRESCRIPTION_IDEMPOTENCY_MISMATCH = "prescription.idempotency_mismatch"
    PRESCRIPTION_DOSING_RULE_INVALID = "prescription.dosing_rule_invalid"
    PRESCRIPTION_DOSING_INPUT_INVALID = "prescription.dosing_input_invalid"
    PRESCRIPTION_ALLERGY_CONFLICT = "prescription.allergy_conflict"
    PRESCRIPTION_PEDIATRIC_WEIGHT_MISSING = "prescription.pediatric_weight_missing"
    PRESCRIPTION_DOSE_ABOVE_MAXIMUM = "prescription.dose_above_maximum"
    PRESCRIPTION_SAFETY_BLOCKED = "prescription.safety_blocked"

    RECALL_NOT_FOUND = "recall.not_found"
    RECALL_VERSION_CONFLICT = "recall.version_conflict"
    RECALL_INVALID_STATUS = "recall.invalid_status"
    RECALL_IDEMPOTENCY_MISMATCH = "recall.idempotency_mismatch"
    RECALL_DUE_REQUIRED = "recall.due_required"
