"""Clinics FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.clinics.service import ClinicService


def get_clinic_service(
    session: AsyncSession = Depends(get_session),
) -> ClinicService:
    return ClinicService(session=session)
