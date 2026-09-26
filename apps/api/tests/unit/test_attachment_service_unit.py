"""Unit tests for AttachmentService with mocked I/O."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from ent.core.errors.exceptions import NotFoundError
from ent.core.security.principal import CurrentUser
from ent.features.attachments.schemas.requests import (
    AttachmentConfirmRequest,
    AttachmentUploadUrlRequest,
)
from ent.features.attachments.service import AttachmentService
from ent.integrations.storage.port import PresignedUrl
from ent.settings import get_settings


def _user(clinic_id: int = 1) -> CurrentUser:
    return CurrentUser(
        user_id=10,
        user_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        session_id=20,
        session_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB0",
        clinic_id=clinic_id,
        clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        permissions=frozenset({"attachment.write", "attachment.read"}),
    )


@pytest.mark.asyncio
async def test_request_upload_url_persists_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    clinic = MagicMock(public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1")
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = clinic
    session.execute.return_value = execute_result

    redis = AsyncMock()
    monkeypatch.setattr(
        "ent.features.attachments.service.get_redis",
        AsyncMock(return_value=redis),
    )

    storage = AsyncMock()
    storage.create_presigned_upload.return_value = PresignedUrl(
        url="local-storage://upload",
        method="PUT",
        expires_in_seconds=900,
        headers={"Content-Type": "image/jpeg"},
    )

    service = AttachmentService(session, settings=get_settings(), storage=storage)
    body = AttachmentUploadUrlRequest(
        category="clinical_photo",
        filename="ear.jpg",
        content_type="image/jpeg",
        size_bytes=512,
    )
    response = await service.request_upload_url(user=_user(), body=body)

    assert response.upload_token
    redis.setex.assert_awaited_once()
    storage.create_presigned_upload.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_upload_missing_pending_token() -> None:
    session = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = None

    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.get_redis",
            AsyncMock(return_value=redis),
        )
        with pytest.raises(NotFoundError):
            await service.confirm_upload(
                user=_user(),
                body=AttachmentConfirmRequest(
                    upload_token="01ARZ3NDEKTSV4RRFFQ69G5FB2",
                ),
            )


@pytest.mark.asyncio
async def test_confirm_upload_wrong_clinic() -> None:
    session = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = json.dumps({"clinic_id": 99, "storage_key": "k"})

    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.get_redis",
            AsyncMock(return_value=redis),
        )
        with pytest.raises(NotFoundError):
            await service.confirm_upload(
                user=_user(clinic_id=1),
                body=AttachmentConfirmRequest(
                    upload_token="01ARZ3NDEKTSV4RRFFQ69G5FB3",
                ),
            )


@pytest.mark.asyncio
async def test_get_attachment_not_found() -> None:
    session = AsyncMock()
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())

    repo_mock = MagicMock()
    repo_mock.get_by_public_id_with_variants = AsyncMock(return_value=None)
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.AttachmentRepository",
            lambda *args, **kwargs: repo_mock,
        )
        with pytest.raises(NotFoundError):
            await service.get_attachment(user=_user(), public_id="missing")


@pytest.mark.asyncio
async def test_confirm_upload_object_missing() -> None:
    session = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = json.dumps(
        {
            "clinic_id": 1,
            "storage_key": "clinic/k.jpg",
            "object_ulid": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "category": "clinical_photo",
            "filename": "a.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 10,
        },
    )
    storage = AsyncMock()
    storage.object_exists.return_value = False

    service = AttachmentService(session, settings=get_settings(), storage=storage)
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.get_redis",
            AsyncMock(return_value=redis),
        )
        from ent.core.errors.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await service.confirm_upload(
                user=_user(clinic_id=1),
                body=AttachmentConfirmRequest(
                    upload_token="01ARZ3NDEKTSV4RRFFQ69G5FB4",
                ),
            )


@pytest.mark.asyncio
async def test_get_attachment_returns_read_model() -> None:
    session = AsyncMock()
    attachment = MagicMock()
    attachment.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    attachment.category = "clinical_photo"
    attachment.filename = "a.jpg"
    attachment.content_type = "image/jpeg"
    attachment.size_bytes = 10
    attachment.checksum_sha256 = None
    attachment.width = None
    attachment.height = None
    attachment.duration_ms = None
    attachment.caption = None
    attachment.processing_status = "ready"
    attachment.patient_public_id = None
    attachment.virus_scanned_at = None
    attachment.captured_at = None
    attachment.variants = []

    repo_mock = MagicMock()
    repo_mock.get_by_public_id_with_variants = AsyncMock(return_value=attachment)
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.AttachmentRepository",
            lambda *args, **kwargs: repo_mock,
        )
        read = await service.get_attachment(
            user=_user(),
            public_id=attachment.public_id,
        )
    assert read.public_id == attachment.public_id


@pytest.mark.asyncio
async def test_request_download_url_original() -> None:
    session = AsyncMock()
    attachment = MagicMock()
    attachment.variants = []
    attachment.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    attachment.storage_key = "k"
    attachment.filename = "a.jpg"
    attachment.id = 1
    attachment.patient_id = None

    repo_mock = MagicMock()
    repo_mock.get_by_public_id_with_variants = AsyncMock(return_value=attachment)
    storage = AsyncMock()
    storage.create_presigned_download.return_value = PresignedUrl(
        url="local-storage://download",
        method="GET",
        expires_in_seconds=300,
        headers={},
    )

    service = AttachmentService(session, settings=get_settings(), storage=storage)
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.AttachmentRepository",
            lambda *args, **kwargs: repo_mock,
        )
        response = await service.request_download_url(
            user=_user(),
            public_id=attachment.public_id,
            variant=None,
        )
    assert response.download.url
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_download_url_variant_not_found() -> None:
    session = AsyncMock()
    attachment = MagicMock()
    attachment.variants = []
    attachment.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    attachment.storage_key = "k"
    attachment.filename = "a.jpg"
    attachment.id = 1
    attachment.patient_id = None

    repo_mock = MagicMock()
    repo_mock.get_by_public_id_with_variants = AsyncMock(return_value=attachment)
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            "ent.features.attachments.service.AttachmentRepository",
            lambda *args, **kwargs: repo_mock,
        )
        with pytest.raises(NotFoundError):
            await service.request_download_url(
                user=_user(),
                public_id=attachment.public_id,
                variant="thumb",
            )
