"""Prescription FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.prescriptions.service import PrescriptionService


def get_prescription_service(
    session: AsyncSession = Depends(get_session),
) -> PrescriptionService:
    return PrescriptionService(session=session)
