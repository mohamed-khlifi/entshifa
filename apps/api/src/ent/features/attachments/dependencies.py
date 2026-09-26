"""Attachments FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.attachments.service import AttachmentService
from ent.settings import Settings, get_settings


def get_attachment_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AttachmentService:
    return AttachmentService(session=session, settings=settings)
