"""Attachment use cases: pre-signed upload/download and confirm."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.schemas.common import CodeableConcept, Laterality
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.attachments.models import ATTACHMENT_CATEGORIES, Attachment
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
from ent.features.clinics.repository import ClinicRepository
from ent.features.patients.models import Patient
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.features.terminology.repository import TerminologyRepository
from ent.integrations.redis import get_redis
from ent.integrations.storage import get_object_storage
from ent.integrations.storage.keys import build_storage_key
from ent.integrations.storage.port import ObjectStorage
from ent.jobs.queue import enqueue_job
from ent.jobs.tasks.process_attachment import JOB_PROCESS_ATTACHMENT
from ent.settings import Settings, get_settings

_BODY_SITE_KIND = "anatomy"
_ALLOWED_CATEGORIES = frozenset(ATTACHMENT_CATEGORIES)

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


def _to_utc_naive(value: datetime) -> datetime:
    """Persist an aware instant as naive UTC DATETIME(6)."""

    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _parse_pending_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return _to_utc_naive(datetime.fromisoformat(value))


def _to_read(
    attachment: Attachment,
    *,
    body_site: CodeableConcept | None = None,
) -> AttachmentRead:
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
        laterality=(
            attachment.laterality if isinstance(attachment.laterality, str) else None
        ),
        body_site=body_site,
        is_consented_for_teaching=bool(attachment.is_consented_for_teaching),
        virus_scanned_at=attachment.virus_scanned_at,
        captured_at=(
            attachment.captured_at
            if isinstance(attachment.captured_at, datetime)
            else None
        ),
        created_at=(
            attachment.created_at
            if isinstance(attachment.created_at, datetime)
            else None
        ),
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
        patient_id: int | None = None
        if body.patient_public_id is not None:
            patient = await self._visible_patient(user, body.patient_public_id)
            patient_id = int(patient.id)
        body_site_id = await self._body_site_id(user, body.body_site_concept_id)
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
            "patient_id": patient_id,
            "caption": body.caption,
            "laterality": (
                body.laterality.value if body.laterality is not None else None
            ),
            "body_site_concept_id": body_site_id,
            "captured_at": (
                _to_utc_naive(body.captured_at).isoformat()
                if body.captured_at is not None
                else None
            ),
            "is_consented_for_teaching": body.is_consented_for_teaching,
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
        content_locale: str = "fr",
    ) -> AttachmentRead:
        redis = await get_redis()
        raw = await redis.get(f"{_PENDING_UPLOAD_PREFIX}{body.upload_token}")
        if raw is None:
            raise NotFoundError(
                resource="attachment_upload", public_id=body.upload_token
            )
        pending: dict[str, Any] = json.loads(raw)
        if int(pending["clinic_id"]) != user.clinic_id:
            raise NotFoundError(
                resource="attachment_upload", public_id=body.upload_token
            )

        storage_key = str(pending["storage_key"])
        if not await self._storage.object_exists(key=storage_key):
            raise ValidationError(reason="upload_incomplete", storageKey=storage_key)

        patient_public_id = pending.get("patient_public_id")
        patient_id: int | None = None
        if isinstance(patient_public_id, str) and patient_public_id:
            patient = await self._visible_patient(user, patient_public_id)
            patient_id = int(patient.id)

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
            caption=(
                pending.get("caption")
                if isinstance(pending.get("caption"), str)
                else None
            ),
            patient_public_id=(
                patient_public_id if isinstance(patient_public_id, str) else None
            ),
            patient_id=patient_id,
            laterality=(
                str(pending["laterality"])
                if isinstance(pending.get("laterality"), str)
                else None
            ),
            body_site_concept_id=(
                int(pending["body_site_concept_id"])
                if isinstance(pending.get("body_site_concept_id"), int)
                else None
            ),
            captured_at=_parse_pending_datetime(pending.get("captured_at")),
            is_consented_for_teaching=bool(pending.get("is_consented_for_teaching")),
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
        return await self._read_one(user, loaded, content_locale)

    async def list_attachments(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        category: str | None,
        laterality: str | None,
        captured_from: datetime | None,
        captured_to: datetime | None,
        page: PaginationParams | None,
        content_locale: str = "fr",
    ) -> PageSchema[AttachmentRead]:
        if category is not None and category not in _ALLOWED_CATEGORIES:
            raise ValidationError(reason="category", category=category)
        if laterality is not None and laterality not in Laterality:
            raise ValidationError(reason="laterality", laterality=laterality)
        start = _to_utc_naive(captured_from) if captured_from is not None else None
        end = _to_utc_naive(captured_to) if captured_to is not None else None
        if start is not None and end is not None and end <= start:
            raise ValidationError(reason="captured_range")

        patient = await self._visible_patient(user, patient_public_id)
        repo = AttachmentRepository(self._session, clinic_id=user.clinic_id)
        result = await repo.list_for_chart(
            patient_id=int(patient.id),
            category=category,
            laterality=laterality,
            captured_from=start,
            captured_to=end,
            page=page,
        )
        sites = await self._body_sites(user, result.items, content_locale)
        AuditRecorder(self._session).record_access(
            action="list",
            entity_type="attachment",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            reason="chart",
        )
        await self._session.commit()
        return PageSchema(
            items=[
                _to_read(
                    row,
                    body_site=(
                        sites.get(int(row.body_site_concept_id))
                        if isinstance(row.body_site_concept_id, int)
                        else None
                    ),
                )
                for row in result.items
            ],
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def get_attachment(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str = "fr",
    ) -> AttachmentRead:
        repo = AttachmentRepository(self._session, clinic_id=user.clinic_id)
        attachment = await repo.get_by_public_id_with_variants(public_id)
        if attachment is None:
            raise NotFoundError(resource="attachment", public_id=public_id)
        read = await self._read_one(user, attachment, content_locale)
        AuditRecorder(self._session).record_access(
            action="read",
            entity_type="attachment",
            clinic_id=user.clinic_id,
            entity_id=attachment.id if isinstance(attachment.id, int) else None,
            entity_public_id=attachment.public_id,
            patient_id=(
                attachment.patient_id
                if isinstance(attachment.patient_id, int)
                else None
            ),
        )
        await self._session.commit()
        return read

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
                (
                    v
                    for v in attachment.variants
                    if v.variant == variant and v.deleted_at is None
                ),
                None,
            )
            if match is None:
                raise NotFoundError(
                    resource="media_variant", public_id=f"{public_id}:{variant}"
                )
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

    async def _read_one(
        self,
        user: CurrentUser,
        attachment: Attachment,
        content_locale: str,
    ) -> AttachmentRead:
        sites = await self._body_sites(user, [attachment], content_locale)
        site = None
        if isinstance(attachment.body_site_concept_id, int):
            site = sites.get(attachment.body_site_concept_id)
        return _to_read(attachment, body_site=site)

    async def _body_sites(
        self,
        user: CurrentUser,
        rows: list[Attachment],
        content_locale: str,
    ) -> dict[int, CodeableConcept]:
        concept_ids = {
            int(row.body_site_concept_id)
            for row in rows
            if isinstance(row.body_site_concept_id, int)
        }
        if not concept_ids:
            return {}
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        default_locale = clinic.default_locale if clinic is not None else "fr"
        labels = await PatientRepository(
            self._session, clinic_id=user.clinic_id
        ).concept_labels(
            concept_ids,
            locale=content_locale,
            clinic_default_locale=default_locale,
        )
        return {
            concept_id: CodeableConcept(
                concept_id=public_id,
                code=code,
                display=display,
            )
            for concept_id, (public_id, code, display) in labels.items()
        }

    async def _visible_patient(self, user: CurrentUser, public_id: str) -> Patient:
        patient = await PatientRepository(
            self._session, clinic_id=user.clinic_id
        ).get_visible(public_id, created_by_id=created_by_scope(user))
        if patient is None:
            raise NotFoundError(resource="patient", public_id=public_id)
        return patient

    async def _body_site_id(
        self, user: CurrentUser, public_id: str | None
    ) -> int | None:
        if public_id is None:
            return None
        concept = await TerminologyRepository(
            self._session, user.clinic_id
        ).get_concept_by_public_id(public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=public_id)
        if concept.kind != _BODY_SITE_KIND:
            raise ValidationError(reason="body_site_kind", kind=concept.kind)
        return int(concept.id)

    async def _clinic(self, clinic_id: int) -> Clinic:
        clinic = await ClinicRepository(self._session).get(clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic", public_id=str(clinic_id))
        return clinic
