"""Recall FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.recalls.service import RecallService


def get_recall_service(
    session: AsyncSession = Depends(get_session),
) -> RecallService:
    return RecallService(session=session)
