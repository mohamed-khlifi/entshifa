"""Import all ORM models so Base.metadata is complete for Alembic."""

from __future__ import annotations

from ent.core.audit.models import AccessLog, AuditLog
from ent.features.auth.models import Permission, Role, RolePermission
from ent.features.clinics.models import Clinic, Site
from ent.features.users.models import User, UserClinicRole, UserSession
from ent.jobs.models import JobRun

__all__ = [
    "AccessLog",
    "AuditLog",
    "Clinic",
    "JobRun",
    "Permission",
    "Role",
    "RolePermission",
    "Site",
    "User",
    "UserClinicRole",
    "UserSession",
]
