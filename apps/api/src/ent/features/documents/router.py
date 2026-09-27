"""Document HTTP endpoints (P1-09)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.documents.dependencies import (
    get_document_service,
    get_document_template_service,
)
from ent.features.documents.schemas.requests import (
    DocumentCreate,
    DocumentFinalize,
    DocumentRecipientCreate,
    DocumentTemplateCreate,
    DocumentTemplateVersionCreate,
)
from ent.features.documents.schemas.responses import (
    DocumentDownloadRead,
    DocumentRead,
    DocumentRecipientRead,
    DocumentTemplateRead,
)
from ent.features.documents.service import DocumentService
from ent.features.documents.templates.service import DocumentTemplateService

router = APIRouter(tags=["documents"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/document-templates", response_model=PageSchema[DocumentTemplateRead]
)
async def list_document_templates(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentTemplateService = Depends(get_document_template_service),
) -> PageSchema[DocumentTemplateRead]:
    return await service.list_templates(user=user, page_params=_page(limit, offset))


@router.post(
    "/api/v1/document-templates",
    response_model=DocumentTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_template(
    body: DocumentTemplateCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_TEMPLATES)),
    service: DocumentTemplateService = Depends(get_document_template_service),
) -> DocumentTemplateRead:
    return await service.create_template(user=user, body=body)


@router.post(
    "/api/v1/document-templates/{template_id}/versions",
    response_model=DocumentTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_document_template_version(
    template_id: str,
    body: DocumentTemplateVersionCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_TEMPLATES)),
    service: DocumentTemplateService = Depends(get_document_template_service),
) -> DocumentTemplateRead:
    return await service.add_template_version(
        user=user,
        template_public_id=template_id,
        body=body,
    )


@router.get("/api/v1/documents", response_model=PageSchema[DocumentRead])
async def list_documents(
    patient_public_id: str = Query(
        min_length=26, max_length=26, alias="patientPublicId"
    ),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentService = Depends(get_document_service),
) -> PageSchema[DocumentRead]:
    return await service.list_documents(
        user=user,
        patient_public_id=patient_public_id,
        page_params=_page(limit, offset),
    )


@router.post(
    "/api/v1/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    body: DocumentCreate,
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    return await service.create_document(user=user, body=body)


@router.get("/api/v1/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: str,
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    return await service.get_document(user=user, public_id=document_id)


@router.post("/api/v1/documents/{document_id}/finalize", response_model=DocumentRead)
async def finalize_document(
    document_id: str,
    body: DocumentFinalize,
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    return await service.finalize_document(user=user, public_id=document_id, body=body)


@router.get(
    "/api/v1/documents/{document_id}/download-url",
    response_model=DocumentDownloadRead,
)
async def document_download_url(
    document_id: str,
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentService = Depends(get_document_service),
) -> DocumentDownloadRead:
    return await service.download_url(user=user, public_id=document_id)


@router.post(
    "/api/v1/documents/{document_id}/recipients",
    response_model=DocumentRecipientRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_document_recipient(
    document_id: str,
    body: DocumentRecipientCreate,
    user: CurrentUser = Depends(require(Permission.DOCUMENT_FINALIZE)),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRecipientRead:
    return await service.add_recipient(user=user, public_id=document_id, body=body)
