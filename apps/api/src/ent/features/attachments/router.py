"""Attachment HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.attachments.dependencies import get_attachment_service
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
) -> AttachmentRead:
    return await service.confirm_upload(user=user, body=body)


@router.get("/{public_id}", response_model=AttachmentRead)
async def get_attachment(
    public_id: str,
    user: CurrentUser = Depends(require(Permission.ATTACHMENT_READ)),
    service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentRead:
    return await service.get_attachment(user=user, public_id=public_id)


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
