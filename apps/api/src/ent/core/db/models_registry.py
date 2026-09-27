"""Import all ORM models so Base.metadata is complete for Alembic."""

from __future__ import annotations

from ent.core.audit.models import AccessLog, AuditLog
from ent.features.attachments.models import Attachment, MediaVariant
from ent.features.auth.models import Permission, Role, RolePermission
from ent.features.clinics.models import Clinic, Setting, Site
from ent.features.documents.models import (
    Document,
    DocumentRecipient,
    DocumentTemplate,
    DocumentTemplateVersion,
    PhraseLibrary,
)
from ent.features.patients.models import (
    Patient,
    PatientAllergy,
    PatientFlag,
    PatientHistory,
    PatientIdentifier,
    PatientMedication,
    PatientMergeLog,
    PatientProblem,
    PatientRequestIdempotency,
)
from ent.features.scheduling.models import Appointment, AppointmentType
from ent.features.terminology.models import (
    CodeSystem,
    Concept,
    ConceptRelationship,
    ConceptTranslation,
    ValueSet,
    ValueSetMember,
)
from ent.features.users.models import (
    PasswordResetToken,
    User,
    UserClinicRole,
    UserInvitation,
    UserSession,
)
from ent.jobs.models import JobRun

__all__ = [
    "Appointment",
    "AppointmentType",
    "AccessLog",
    "Attachment",
    "AuditLog",
    "Clinic",
    "CodeSystem",
    "Document",
    "DocumentRecipient",
    "DocumentTemplate",
    "DocumentTemplateVersion",
    "Setting",
    "Concept",
    "ConceptRelationship",
    "ConceptTranslation",
    "JobRun",
    "MediaVariant",
    "PasswordResetToken",
    "Patient",
    "PatientAllergy",
    "PatientFlag",
    "PatientHistory",
    "PatientIdentifier",
    "PatientMedication",
    "PatientMergeLog",
    "PatientProblem",
    "PatientRequestIdempotency",
    "Permission",
    "PhraseLibrary",
    "Role",
    "RolePermission",
    "Site",
    "User",
    "UserClinicRole",
    "UserInvitation",
    "UserSession",
    "ValueSet",
    "ValueSetMember",
]
