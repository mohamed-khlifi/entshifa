"""Patients FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.core.errors.exceptions import PermissionDeniedError
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import get_current_user
from ent.features.patients.service import PatientService


def get_patient_service(
    session: AsyncSession = Depends(get_session),
) -> PatientService:
    return PatientService(session=session)


def require_patient_read() -> Callable[..., Awaitable[CurrentUser]]:
    async def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        allowed = {
            Permission.PATIENT_READ_CLINIC.value,
            Permission.PATIENT_READ_OWN.value,
        }
        if user.permissions.isdisjoint(allowed):
            raise PermissionDeniedError(permission=Permission.PATIENT_READ_OWN.value)
        return user

    return _dependency
