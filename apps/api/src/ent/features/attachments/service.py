"""Attachment use cases: pre-signed upload/download and confirm."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.attachments.models import Attachment
from ent.features.attachments.repository import AttachmentRepository
from ent.features.attachments.schemas.requests import (
    AttachmentConfirmRequest,
    AttachmentUploadUrlRequest,
)
from ent.features.attachments.schemas.responses import (
    AttachmentDownloadUrlResponse,
    AttachmentRead,
    AttachmentUploadUrlResponse,
    MediaVariantRead,
    PresignedUrlResponse,
)
from ent.features.clinics.models import Clinic
from ent.integrations.redis import get_redis
from ent.integrations.storage import get_object_storage
from ent.integrations.storage.keys import build_storage_key
from ent.integrations.storage.port import ObjectStorage
from ent.jobs.queue import enqueue_job
from ent.jobs.tasks.process_attachment import JOB_PROCESS_ATTACHMENT
from ent.settings import Settings, get_settings

_PENDING_UPLOAD_PREFIX = "ent:attachments:pending:"


def _extension_for(filename: str, content_type: str) -> str:
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    mapping = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pdf": "pdf",
        "video/mp4": "mp4",
        "audio/mpeg": "mp3",
    }
    return mapping.get(content_type.lower(), "bin")


def _to_read(attachment: Attachment) -> AttachmentRead:
    variants = [
        MediaVariantRead(
            public_id=v.public_id,
            variant=v.variant,
            width=v.width,
            height=v.height,
            size_bytes=int(v.size_bytes),
            content_type=v.content_type,
        )
        for v in (attachment.variants or [])
        if v.deleted_at is None
    ]
    return AttachmentRead(
        public_id=attachment.public_id,
        category=attachment.category,
        filename=attachment.filename,
        content_type=attachment.content_type,
        size_bytes=int(attachment.size_bytes),
        checksum_sha256=attachment.checksum_sha256,
        width=attachment.width,
        height=attachment.height,
        duration_ms=attachment.duration_ms,
        caption=attachment.caption,
        processing_status=attachment.processing_status,
        patient_public_id=attachment.patient_public_id,
        virus_scanned_at=attachment.virus_scanned_at,
        captured_at=attachment.captured_at,
        variants=variants,
    )


class AttachmentService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings | None = None,
        storage: ObjectStorage | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._storage = storage or get_object_storage(self._settings)

    async def request_upload_url(
        self,
        *,
        user: CurrentUser,
        body: AttachmentUploadUrlRequest,
    ) -> AttachmentUploadUrlResponse:
        clinic = await self._clinic(user.clinic_id)
        object_ulid = new_ulid()
        upload_token = new_ulid()
        ext = _extension_for(body.filename, body.content_type)
        storage_key = build_storage_key(
            clinic_public_id=clinic.public_id,
            patient_public_id=body.patient_public_id,
            category=body.category,
            object_ulid=object_ulid,
            extension=ext,
        )
        ttl = self._settings.attachment_upload_url_ttl_seconds
        presigned = await self._storage.create_presigned_upload(
            key=storage_key,
            content_type=body.content_type,
            expires_in_seconds=ttl,
        )
        pending = {
            "clinic_id": user.clinic_id,
            "clinic_public_id": clinic.public_id,
            "user_id": user.user_id,
            "storage_key": storage_key,
            "category": body.category,
            "filename": body.filename,
            "content_type": body.content_type,
            "size_bytes": body.size_bytes,
            "patient_public_id": body.patient_public_id,
            "caption": body.caption,
            "object_ulid": object_ulid,
        }
        redis = await get_redis()
        await redis.setex(
            f"{_PENDING_UPLOAD_PREFIX}{upload_token}",
            ttl,
            json.dumps(pending, separators=(",", ":"), sort_keys=True),
        )
        return AttachmentUploadUrlResponse(
            upload_token=upload_token,
            storage_key=storage_key,
            upload=PresignedUrlResponse(
                url=presigned.url,
                method=presigned.method,
                expires_in_seconds=presigned.expires_in_seconds,
                headers=presigned.headers,
            ),
        )

    async def confirm_upload(
        self,
        *,
        user: CurrentUser,
        body: AttachmentConfirmRequest,
    ) -> AttachmentRead:
        redis = await get_redis()
        raw = await redis.get(f"{_PENDING_UPLOAD_PREFIX}{body.upload_token}")
        if raw is None:
            raise NotFoundError(resource="attachment_upload", public_id=body.upload_token)
        pending: dict[str, Any] = json.loads(raw)
        if int(pending["clinic_id"]) != user.clinic_id:
            raise NotFoundError(resource="attachment_upload", public_id=body.upload_token)

        storage_key = str(pending["storage_key"])
        if not await self._storage.object_exists(key=storage_key):
            raise ValidationError(reason="upload_incomplete", storageKey=storage_key)

        repo = AttachmentRepository(self._session, clinic_id=user.clinic_id)
        existing = await repo.get_by_storage_key(storage_key)
        if existing is not None:
            raise ConflictError(reason="already_confirmed", publicId=existing.public_id)

        attachment = Attachment(
            clinic_id=user.clinic_id,
            public_id=str(pending["object_ulid"]),
            category=str(pending["category"]),
            storage_key=storage_key,
            filename=str(pending["filename"]),
            content_type=str(pending["content_type"]),
            size_bytes=int(pending["size_bytes"]),
            caption=pending.get("caption"),
            patient_public_id=pending.get("patient_public_id"),
            captured_by_id=user.user_id,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
            processing_status="pending",
        )
        await repo.add(attachment)
        AuditRecorder(self._session).record_entity_create(attachment)
        await self._session.commit()
        await self._session.refresh(attachment)

        await redis.delete(f"{_PENDING_UPLOAD_PREFIX}{body.upload_token}")
        await enqueue_job(
            job_name=JOB_PROCESS_ATTACHMENT,
            idempotency_key=f"process-attachment:{attachment.public_id}",
            payload={"attachment_public_id": attachment.public_id},
        )
        # Reload empty variants list for response shape.
        loaded = await repo.get_by_public_id_with_variants(attachment.public_id)
        assert loaded is not None
        return _to_read(loaded)

    async def get_attachment(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AttachmentRead:
        repo = AttachmentRepository(self._session, clinic_id=user.clinic_id)
        attachment = await repo.get_by_public_id_with_variants(public_id)
        if attachment is None:
            raise NotFoundError(resource="attachment", public_id=public_id)
        return _to_read(attachment)

    async def request_download_url(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        variant: str | None = None,
    ) -> AttachmentDownloadUrlResponse:
        repo = AttachmentRepository(self._session, clinic_id=user.clinic_id)
        attachment = await repo.get_by_public_id_with_variants(public_id)
        if attachment is None:
            raise NotFoundError(resource="attachment", public_id=public_id)

        storage_key = attachment.storage_key
        filename = attachment.filename
        if variant:
            match = next(
                (v for v in attachment.variants if v.variant == variant and v.deleted_at is None),
                None,
            )
            if match is None:
                raise NotFoundError(resource="media_variant", public_id=f"{public_id}:{variant}")
            storage_key = match.storage_key
            stem = attachment.filename.rsplit(".", 1)[0]
            filename = f"{stem}_{variant}.jpg"

        ttl = self._settings.attachment_download_url_ttl_seconds
        presigned = await self._storage.create_presigned_download(
            key=storage_key,
            expires_in_seconds=ttl,
            filename=filename,
        )
        AuditRecorder(self._session).record_access(
            action="download",
            entity_type="attachment",
            clinic_id=user.clinic_id,
            entity_id=attachment.id,
            entity_public_id=attachment.public_id,
            patient_id=attachment.patient_id,
            reason=f"variant={variant or 'original'}",
        )
        await self._session.commit()

        return AttachmentDownloadUrlResponse(
            attachment_public_id=attachment.public_id,
            variant=variant,
            download=PresignedUrlResponse(
                url=presigned.url,
                method=presigned.method,
                expires_in_seconds=presigned.expires_in_seconds,
                headers=presigned.headers,
            ),
        )

    async def _clinic(self, clinic_id: int) -> Clinic:
        result = await self._session.execute(
            select(Clinic).where(Clinic.id == clinic_id, Clinic.deleted_at.is_(None)),
        )
        clinic = result.scalar_one_or_none()
        if clinic is None:
            raise NotFoundError(resource="clinic", public_id=str(clinic_id))
        return clinic
