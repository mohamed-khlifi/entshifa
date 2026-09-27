"""Attachment HTTP endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.attachments.dependencies import (
    get_attachment_service,
    get_content_locale,
)
from ent.features.attachments.schemas.requests import (
    AttachmentConfirmRequest,
    AttachmentUploadUrlRequest,
)
from ent.features.attachments.schemas.responses import (
    AttachmentDownloadUrlResponse,
    AttachmentRead,
    AttachmentUploadUrlResponse,
)
from ent.features.attachments.service import AttachmentService
from ent.features.auth.dependencies import require

router = APIRouter(prefix="/api/v1/attachments", tags=["attachments"])


@router.get("", response_model=PageSchema[AttachmentRead])
async def list_attachments(
    patient_public_id: str = Query(
        ..., alias="patientPublicId", min_length=26, max_length=26
    ),
    category: str | None = Query(default=None, max_length=40),
    laterality: str | None = Query(default=None, max_length=20),
    captured_from: datetime | None = Query(default=None, alias="capturedFrom"),
    captured_to: datetime | None = Query(default=None, alias="capturedTo"),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.ATTACHMENT_READ)),
    service: AttachmentService = Depends(get_attachment_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[AttachmentRead]:
    return await service.list_attachments(
        user=user,
        patient_public_id=patient_public_id,
        category=category,
        laterality=laterality,
        captured_from=captured_from,
        captured_to=captured_to,
        page=PaginationParams(limit=limit, offset=offset),
        content_locale=content_locale,
    )


@router.post("/upload-url", response_model=AttachmentUploadUrlResponse)
async def create_upload_url(
    body: AttachmentUploadUrlRequest,
    user: CurrentUser = Depends(require(Permission.ATTACHMENT_WRITE)),
    service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentUploadUrlResponse:
    return await service.request_upload_url(user=user, body=body)


@router.post("/confirm", response_model=AttachmentRead)
async def confirm_upload(
    body: AttachmentConfirmRequest,
    user: CurrentUser = Depends(require(Permission.ATTACHMENT_WRITE)),
    service: AttachmentService = Depends(get_attachment_service),
    content_locale: str = Depends(get_content_locale),
) -> AttachmentRead:
    return await service.confirm_upload(
        user=user, body=body, content_locale=content_locale
    )


@router.get("/{public_id}", response_model=AttachmentRead)
async def get_attachment(
    public_id: str,
    user: CurrentUser = Depends(require(Permission.ATTACHMENT_READ)),
    service: AttachmentService = Depends(get_attachment_service),
    content_locale: str = Depends(get_content_locale),
) -> AttachmentRead:
    return await service.get_attachment(
        user=user, public_id=public_id, content_locale=content_locale
    )


@router.get("/{public_id}/download-url", response_model=AttachmentDownloadUrlResponse)
async def create_download_url(
    public_id: str,
    variant: str | None = Query(default=None, max_length=20),
    user: CurrentUser = Depends(require(Permission.ATTACHMENT_READ)),
    service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentDownloadUrlResponse:
    return await service.request_download_url(
        user=user,
        public_id=public_id,
        variant=variant,
    )
