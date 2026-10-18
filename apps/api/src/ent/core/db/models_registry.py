"""Import all ORM models so Base.metadata is complete for Alembic."""

from __future__ import annotations

from ent.core.audit.models import AccessLog, AuditLog
from ent.features.attachments.models import Attachment, MediaVariant
from ent.features.audiology.models import (
    Audiogram,
    AudiogramThreshold,
    AudiologyRequestIdempotency,
)
from ent.features.auth.models import Permission, Role, RolePermission
from ent.features.clinics.models import Clinic, ReferenceDataVersion, Setting, Site
from ent.features.diagnoses.models import Diagnosis, UserDiagnosisFavorite
from ent.features.documents.models import (
    Document,
    DocumentRecipient,
    DocumentTemplate,
    DocumentTemplateVersion,
    PhraseLibrary,
)
from ent.features.encounters.models import (
    Encounter,
    EncounterAddendum,
    EncounterComplaint,
    EncounterSignature,
    EncounterTemplate,
)
from ent.features.endoscopy.models import EndoscopyExam
from ent.features.laryngoscopy.models import LaryngoscopyExam
from ent.features.observations.models import (
    ExaminationSnapshot,
    Observation,
    ObservationComponent,
)
from ent.features.otology.models import EarDevice, OfficeProcedure, OtologyExam
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
from ent.features.prescriptions.models import (
    CalculationResultRow,
    Drug,
    DrugForm,
    FormularyEntry,
    Prescription,
    PrescriptionItem,
    PrescriptionRequestIdempotency,
    PrescriptionTemplate,
)
from ent.features.procedures.models import ProcedureRecord, ProcedureRecordAddendum
from ent.features.recalls.models import (
    Protocol,
    ProtocolRule,
    Recall,
    RecallAction,
    RecallRequestIdempotency,
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
    "Audiogram",
    "AudiogramThreshold",
    "AudiologyRequestIdempotency",
    "AuditLog",
    "CalculationResultRow",
    "Clinic",
    "Drug",
    "DrugForm",
    "FormularyEntry",
    "CodeSystem",
    "Diagnosis",
    "Document",
    "DocumentRecipient",
    "DocumentTemplate",
    "DocumentTemplateVersion",
    "Encounter",
    "EncounterAddendum",
    "EncounterComplaint",
    "EncounterSignature",
    "EncounterTemplate",
    "EndoscopyExam",
    "EarDevice",
    "LaryngoscopyExam",
    "ExaminationSnapshot",
    "Setting",
    "Concept",
    "ConceptRelationship",
    "ConceptTranslation",
    "JobRun",
    "MediaVariant",
    "Observation",
    "ObservationComponent",
    "OfficeProcedure",
    "OtologyExam",
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
    "Prescription",
    "PrescriptionItem",
    "PrescriptionRequestIdempotency",
    "PrescriptionTemplate",
    "ProcedureRecord",
    "ProcedureRecordAddendum",
    "Protocol",
    "ProtocolRule",
    "Recall",
    "RecallAction",
    "RecallRequestIdempotency",
    "PhraseLibrary",
    "ReferenceDataVersion",
    "Role",
    "RolePermission",
    "Site",
    "User",
    "UserClinicRole",
    "UserInvitation",
    "UserDiagnosisFavorite",
    "UserSession",
    "ValueSet",
    "ValueSetMember",
]
