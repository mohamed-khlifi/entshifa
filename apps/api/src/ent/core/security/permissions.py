"""Permission codes and the default system role matrix (architecture section 29)."""

from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    PATIENT_READ_OWN = "patient.read.own"
    PATIENT_READ_CLINIC = "patient.read.clinic"
    PATIENT_WRITE = "patient.write"
    PATIENT_MERGE = "patient.merge"
    ENCOUNTER_CREATE = "encounter.create"
    ENCOUNTER_WRITE = "encounter.write"
    ENCOUNTER_SIGN = "encounter.sign"
    ENCOUNTER_AMEND = "encounter.amend"
    PRESCRIPTION_CREATE = "prescription.create"
    PRESCRIPTION_SIGN = "prescription.sign"
    AUDIOLOGY_ENTER = "audiology.enter"
    AUDIOLOGY_INTERPRET = "audiology.interpret"
    SURGERY_SCHEDULE = "surgery.schedule"
    SURGERY_NOTE_WRITE = "surgery.note.write"
    DOCUMENT_FINALIZE = "document.finalize"
    DOCUMENT_SEND = "document.send"
    ADMIN_USERS = "admin.users"
    ADMIN_TEMPLATES = "admin.templates"
    ADMIN_TERMINOLOGY = "admin.terminology"
    ADMIN_EXPORT = "admin.export"
    AUTH_SESSION_READ = "auth.session.read"


SYSTEM_ROLE_MATRIX: dict[str, frozenset[Permission]] = {
    "clinic_admin": frozenset(Permission),
    "doctor": frozenset(
        {
            Permission.PATIENT_READ_CLINIC,
            Permission.PATIENT_WRITE,
            Permission.ENCOUNTER_CREATE,
            Permission.ENCOUNTER_WRITE,
            Permission.ENCOUNTER_SIGN,
            Permission.ENCOUNTER_AMEND,
            Permission.PRESCRIPTION_CREATE,
            Permission.PRESCRIPTION_SIGN,
            Permission.AUDIOLOGY_ENTER,
            Permission.AUDIOLOGY_INTERPRET,
            Permission.SURGERY_SCHEDULE,
            Permission.SURGERY_NOTE_WRITE,
            Permission.DOCUMENT_FINALIZE,
            Permission.DOCUMENT_SEND,
            Permission.AUTH_SESSION_READ,
        }
    ),
    "assistant": frozenset(
        {
            Permission.PATIENT_READ_CLINIC,
            Permission.PATIENT_WRITE,
            Permission.ENCOUNTER_CREATE,
            Permission.ENCOUNTER_WRITE,
            Permission.AUDIOLOGY_ENTER,
            Permission.AUTH_SESSION_READ,
        }
    ),
    "audiology_technician": frozenset(
        {
            Permission.PATIENT_READ_CLINIC,
            Permission.AUDIOLOGY_ENTER,
            Permission.AUTH_SESSION_READ,
        }
    ),
    "read_only": frozenset(
        {
            Permission.PATIENT_READ_CLINIC,
            Permission.AUTH_SESSION_READ,
        }
    ),
}


def permission_codes_for_role(role_code: str) -> frozenset[str]:
    perms = SYSTEM_ROLE_MATRIX.get(role_code, frozenset())
    return frozenset(code.value for code in perms)
