"""Attachments FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.core.i18n.content_locale import content_locale_from_accept_language
from ent.features.attachments.service import AttachmentService
from ent.settings import Settings, get_settings


def get_attachment_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AttachmentService:
    return AttachmentService(session=session, settings=settings)


def get_content_locale(
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
) -> str:
    return content_locale_from_accept_language(accept_language)
