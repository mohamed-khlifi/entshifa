"""Diagnosis FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.diagnoses.service import DiagnosisService


def get_diagnosis_service(
    session: AsyncSession = Depends(get_session),
) -> DiagnosisService:
    return DiagnosisService(session=session)
