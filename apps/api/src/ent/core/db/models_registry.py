"""Import all ORM models so Base.metadata is complete for Alembic."""

from __future__ import annotations

from ent.core.audit.models import AccessLog, AuditLog
from ent.features.attachments.models import Attachment, MediaVariant
from ent.features.auth.models import Permission, Role, RolePermission
from ent.features.clinics.models import Clinic, Site
from ent.features.terminology.models import (
    CodeSystem,
    Concept,
    ConceptRelationship,
    ConceptTranslation,
    ValueSet,
    ValueSetMember,
)
from ent.features.users.models import User, UserClinicRole, UserSession
from ent.jobs.models import JobRun

__all__ = [
    "AccessLog",
    "Attachment",
    "AuditLog",
    "Clinic",
    "CodeSystem",
    "Concept",
    "ConceptRelationship",
    "ConceptTranslation",
    "JobRun",
    "MediaVariant",
    "Permission",
    "Role",
    "RolePermission",
    "Site",
    "User",
    "UserClinicRole",
    "UserSession",
    "ValueSet",
    "ValueSetMember",
]
