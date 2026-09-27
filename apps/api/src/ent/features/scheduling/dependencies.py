"""Scheduling FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.scheduling.service import SchedulingService


def get_scheduling_service(
    session: AsyncSession = Depends(get_session),
) -> SchedulingService:
    return SchedulingService(session=session)
