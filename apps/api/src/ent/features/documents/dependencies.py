"""Document FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.documents.service import DocumentService
from ent.features.documents.templates.service import DocumentTemplateService
from ent.settings import Settings, get_settings


def get_document_template_service(
    session: AsyncSession = Depends(get_session),
) -> DocumentTemplateService:
    return DocumentTemplateService(session=session)


def get_document_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    return DocumentService(session=session, settings=settings)
