"""Terminology FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.terminology.service import TerminologyService


def get_terminology_service(
    session: AsyncSession = Depends(get_session),
) -> TerminologyService:
    return TerminologyService(session=session)
