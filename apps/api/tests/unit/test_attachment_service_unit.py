"""Unit tests for AttachmentService with mocked I/O."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
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


def _clinician() -> CurrentUser:
    user = _user()
    return replace(
        user,
        permissions=frozenset({*user.permissions, "patient.read.clinic"}),
    )


@pytest.mark.asyncio
async def test_request_upload_url_stores_chart_metadata(
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
    monkeypatch.setattr(
        "ent.features.attachments.service.PatientRepository",
        lambda *args, **kwargs: MagicMock(
            get_visible=AsyncMock(return_value=MagicMock(id=9)),
        ),
    )
    monkeypatch.setattr(
        "ent.features.attachments.service.TerminologyRepository",
        lambda *args, **kwargs: MagicMock(
            get_concept_by_public_id=AsyncMock(
                return_value=MagicMock(id=4, kind="anatomy"),
            ),
        ),
    )

    storage = AsyncMock()
    storage.create_presigned_upload.return_value = PresignedUrl(
        url="https://storage.example/upload",
        method="PUT",
        expires_in_seconds=900,
        headers={"Content-Type": "video/mp4"},
    )
    service = AttachmentService(session, settings=get_settings(), storage=storage)
    captured = datetime(2026, 9, 27, 8, 30, tzinfo=UTC)
    await service.request_upload_url(
        user=_clinician(),
        body=AttachmentUploadUrlRequest(
            category="endoscopy_video",
            filename="scope.mp4",
            content_type="video/mp4",
            size_bytes=200_000_000,
            patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
            laterality="left",
            body_site_concept_id="01ARZ3NDEKTSV4RRFFQ69G5FB9",
            captured_at=captured,
            is_consented_for_teaching=True,
            caption="Left nasal cavity",
        ),
    )
    pending = json.loads(redis.setex.await_args.args[2])
    assert pending["is_consented_for_teaching"] is True
    assert pending["laterality"] == "left"
    assert pending["body_site_concept_id"] == 4
    assert pending["patient_id"] == 9
    assert pending["size_bytes"] == 200_000_000
    storage.create_presigned_upload.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_upload_url_unknown_patient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = MagicMock(public_id="c")
    session.execute.return_value = execute_result
    monkeypatch.setattr(
        "ent.features.attachments.service.PatientRepository",
        lambda *args, **kwargs: MagicMock(get_visible=AsyncMock(return_value=None)),
    )
    storage = AsyncMock()
    service = AttachmentService(session, settings=get_settings(), storage=storage)
    with pytest.raises(NotFoundError):
        await service.request_upload_url(
            user=_clinician(),
            body=AttachmentUploadUrlRequest(
                category="clinical_photo",
                filename="ear.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
            ),
        )
    storage.create_presigned_upload.assert_not_awaited()


@pytest.mark.asyncio
async def test_request_upload_url_unknown_body_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = MagicMock(public_id="c")
    session.execute.return_value = execute_result
    monkeypatch.setattr(
        "ent.features.attachments.service.TerminologyRepository",
        lambda *args, **kwargs: MagicMock(
            get_concept_by_public_id=AsyncMock(return_value=None),
        ),
    )
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())
    with pytest.raises(NotFoundError):
        await service.request_upload_url(
            user=_user(),
            body=AttachmentUploadUrlRequest(
                category="clinical_photo",
                filename="ear.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                body_site_concept_id="01ARZ3NDEKTSV4RRFFQ69G5FB9",
            ),
        )


@pytest.mark.asyncio
async def test_request_upload_url_rejects_non_anatomy_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = MagicMock(public_id="c")
    session.execute.return_value = execute_result
    monkeypatch.setattr(
        "ent.features.attachments.service.TerminologyRepository",
        lambda *args, **kwargs: MagicMock(
            get_concept_by_public_id=AsyncMock(
                return_value=MagicMock(id=4, kind="drug"),
            ),
        ),
    )
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())
    from ent.core.errors.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await service.request_upload_url(
            user=_user(),
            body=AttachmentUploadUrlRequest(
                category="clinical_photo",
                filename="ear.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                body_site_concept_id="01ARZ3NDEKTSV4RRFFQ69G5FB9",
            ),
        )


@pytest.mark.asyncio
async def test_confirm_upload_persists_teaching_consent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ent.features.attachments.models import Attachment

    session = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = json.dumps(
        {
            "clinic_id": 1,
            "storage_key": "clinic/k.jpg",
            "object_ulid": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "category": "audiogram_scan",
            "filename": "audio.pdf",
            "content_type": "application/pdf",
            "size_bytes": 10,
            "caption": "Outside audiogram",
            "laterality": "right",
            "captured_at": "2026-09-27T10:00:00+00:00",
            "is_consented_for_teaching": True,
        },
    )
    storage = AsyncMock()
    storage.object_exists.return_value = True
    stored: dict[str, Attachment] = {}

    class _Repo:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        async def get_by_storage_key(self, _key: str) -> None:
            return None

        async def add(self, entity: Attachment) -> Attachment:
            entity.variants = []
            stored["row"] = entity
            return entity

        async def get_by_public_id_with_variants(self, _public_id: str) -> Attachment:
            return stored["row"]

    monkeypatch.setattr(
        "ent.features.attachments.service.get_redis", AsyncMock(return_value=redis)
    )
    monkeypatch.setattr("ent.features.attachments.service.AttachmentRepository", _Repo)
    monkeypatch.setattr("ent.features.attachments.service.enqueue_job", AsyncMock())

    service = AttachmentService(session, settings=get_settings(), storage=storage)
    read = await service.confirm_upload(
        user=_user(),
        body=AttachmentConfirmRequest(upload_token="01ARZ3NDEKTSV4RRFFQ69G5FB4"),
    )
    assert read.is_consented_for_teaching is True
    assert read.laterality == "right"
    assert read.category == "audiogram_scan"
    assert stored["row"].captured_at == datetime(2026, 9, 27, 10, 0)
    redis.delete.assert_awaited()


@pytest.mark.asyncio
async def test_list_attachments_resolves_body_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ent.core.repository.pagination import Page
    from ent.core.schemas.base import PaginationParams

    session = AsyncMock()
    item = MagicMock()
    item.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FB0"
    item.category = "endoscopy_image"
    item.filename = "meatus.jpg"
    item.content_type = "image/jpeg"
    item.size_bytes = 20
    item.checksum_sha256 = None
    item.width = None
    item.height = None
    item.duration_ms = None
    item.caption = None
    item.processing_status = "ready"
    item.patient_public_id = "01ARZ3NDEKTSV4RRFFQ69G5FB8"
    item.laterality = "left"
    item.body_site_concept_id = 4
    item.is_consented_for_teaching = True
    item.virus_scanned_at = None
    item.captured_at = None
    item.created_at = datetime(2026, 9, 27, 9, 0, tzinfo=UTC)
    item.variants = []

    class _Repo:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        async def list_for_chart(self, **_kwargs: object) -> Page[MagicMock]:
            return Page(items=[item], total=1, limit=24, offset=0)

    class _Patients:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        async def get_visible(
            self, _public_id: str, *, created_by_id: int | None
        ) -> MagicMock:
            return MagicMock(id=3)

        async def concept_labels(
            self,
            _ids: set[int],
            *,
            locale: str,
            clinic_default_locale: str,
        ) -> dict[int, tuple[str, str, str]]:
            return {4: ("01ARZ3NDEKTSV4RRFFQ69G5FB9", "middle-meatus", "Middle meatus")}

    monkeypatch.setattr("ent.features.attachments.service.AttachmentRepository", _Repo)
    monkeypatch.setattr("ent.features.attachments.service.PatientRepository", _Patients)
    monkeypatch.setattr(
        "ent.features.attachments.service.ClinicRepository",
        lambda *_args, **_kwargs: MagicMock(
            get=AsyncMock(return_value=MagicMock(default_locale="en"))
        ),
    )
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())
    page = await service.list_attachments(
        user=_clinician(),
        patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
        category="endoscopy_image",
        laterality="left",
        captured_from=None,
        captured_to=None,
        page=PaginationParams(limit=24, offset=0),
        content_locale="en",
    )
    assert page.page.total == 1
    assert page.items[0].body_site is not None
    assert page.items[0].body_site.display == "Middle meatus"
    assert page.items[0].is_consented_for_teaching is True
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_list_attachments_rejects_bad_filters() -> None:
    from ent.core.errors.exceptions import ValidationError

    service = AttachmentService(
        AsyncMock(), settings=get_settings(), storage=AsyncMock()
    )
    with pytest.raises(ValidationError):
        await service.list_attachments(
            user=_clinician(),
            patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
            category="not_a_category",
            laterality=None,
            captured_from=None,
            captured_to=None,
            page=None,
        )
    with pytest.raises(ValidationError):
        await service.list_attachments(
            user=_clinician(),
            patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
            category=None,
            laterality="sideways",
            captured_from=None,
            captured_to=None,
            page=None,
        )
    start = datetime(2026, 9, 28, tzinfo=UTC)
    end = datetime(2026, 9, 27, tzinfo=UTC)
    with pytest.raises(ValidationError):
        await service.list_attachments(
            user=_clinician(),
            patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
            category=None,
            laterality=None,
            captured_from=start,
            captured_to=end,
            page=None,
        )


@pytest.mark.asyncio
async def test_list_attachments_unknown_patient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ent.features.attachments.service.PatientRepository",
        lambda *_args, **_kwargs: MagicMock(get_visible=AsyncMock(return_value=None)),
    )
    service = AttachmentService(
        AsyncMock(), settings=get_settings(), storage=AsyncMock()
    )
    with pytest.raises(NotFoundError):
        await service.list_attachments(
            user=_clinician(),
            patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB8",
            category=None,
            laterality=None,
            captured_from=None,
            captured_to=None,
            page=None,
        )


@pytest.mark.asyncio
async def test_get_attachment_resolves_body_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    attachment.created_at = datetime(2026, 9, 27, 9, 0)
    attachment.laterality = "left"
    attachment.is_consented_for_teaching = False
    attachment.body_site_concept_id = 4
    attachment.id = 1
    attachment.patient_id = None
    attachment.variants = []

    class _Patients:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        async def concept_labels(
            self,
            _ids: set[int],
            *,
            locale: str,
            clinic_default_locale: str,
        ) -> dict[int, tuple[str, str, str]]:
            return {4: ("01ARZ3NDEKTSV4RRFFQ69G5FB9", "pinna", "Pinna")}

    monkeypatch.setattr(
        "ent.features.attachments.service.AttachmentRepository",
        lambda *_args, **_kwargs: MagicMock(
            get_by_public_id_with_variants=AsyncMock(return_value=attachment),
        ),
    )
    monkeypatch.setattr("ent.features.attachments.service.PatientRepository", _Patients)
    monkeypatch.setattr(
        "ent.features.attachments.service.ClinicRepository",
        lambda *_args, **_kwargs: MagicMock(
            get=AsyncMock(return_value=MagicMock(default_locale="fr")),
        ),
    )
    service = AttachmentService(session, settings=get_settings(), storage=AsyncMock())
    read = await service.get_attachment(user=_user(), public_id=attachment.public_id)
    assert read.body_site is not None
    assert read.body_site.code == "pinna"
