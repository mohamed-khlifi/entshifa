"""Unit tests for document services with mocked persistence."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from ent.core.errors.exceptions import (
    DocumentImmutableError,
    DocumentNotRenderedError,
    DocumentSyntaxError,
    DocumentTemplateError,
    NotFoundError,
    ValidationError,
)
from ent.core.repository.pagination import Page
from ent.core.schemas.base import PaginationParams
from ent.core.security.principal import CurrentUser
from ent.features.documents.models import Document, DocumentTemplateVersion
from ent.features.documents.schemas.requests import (
    DocumentCreate,
    DocumentFinalize,
    DocumentRecipientCreate,
    DocumentTemplateCreate,
    DocumentTemplatePreview,
    DocumentTemplateVersionCreate,
    PageSetup,
    PlaceholderSpec,
)
from ent.features.documents.service import DocumentService
from ent.features.documents.templates.service import DocumentTemplateService
from ent.integrations.storage.port import PresignedUrl

PATIENT_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
TEMPLATE_ID = "01ARZ3NDEKTSV4RRFFQ69G5FB2"


def _user() -> CurrentUser:
    return CurrentUser(
        user_id=10,
        user_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB3",
        session_id=20,
        session_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB4",
        clinic_id=1,
        clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        permissions=frozenset({"document.finalize", "admin.templates"}),
    )


def _patient() -> SimpleNamespace:
    return SimpleNamespace(
        id=2,
        public_id=PATIENT_ID,
        preferred_locale="en",
        created_by_id=10,
    )


def _template(*, clinic_id: int | None = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=3,
        public_id=TEMPLATE_ID,
        clinic_id=clinic_id,
        code="patient_summary",
        category="patient_summary",
        placeholders={"patient.fullName": {"type": "string", "required": True}},
        is_system=clinic_id is None,
        is_active=True,
    )


def _version() -> DocumentTemplateVersion:
    row = DocumentTemplateVersion(
        clinic_id=1,
        document_template_id=3,
        version=1,
        locale="ar",
        direction="rtl",
        header_html="",
        body_html="<p>{{ patient.fullName }}</p>",
        footer_html="",
        css="",
        page_setup={"title": "ملخص المريض"},
        created_by_id=10,
        updated_by_id=10,
    )
    row.id = 4
    return row


def _document(*, status: str = "draft") -> Document:
    row = Document(
        clinic_id=1,
        patient_id=2,
        template_id=3,
        template_version_id=4,
        category="patient_summary",
        locale="ar",
        title="ملخص المريض",
        status=status,
        content_snapshot={"data": {"patient": {"fullName": "A"}}},
        created_by_id=10,
        updated_by_id=10,
    )
    row.id = 9
    row.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FB6"
    return row


def _page_setup() -> PageSetup:
    return PageSetup(title="Note")


class _Templates:
    def __init__(self, session: MagicMock, clinic_id: int | None = None) -> None:
        self.session = session
        self.by_code: SimpleNamespace | None = _template()
        self.by_public: SimpleNamespace | None = _template()
        self.by_id: SimpleNamespace | None = _template()
        self.active = Page(items=[_template()], total=1, limit=50, offset=0)

    async def get_by_code(self, code: str) -> SimpleNamespace | None:
        if self.by_code is not None and self.by_code.code == code:
            return self.by_code
        return None

    async def get_by_public_id(self, public_id: str) -> SimpleNamespace | None:
        return self.by_public

    async def get(self, template_id: int) -> SimpleNamespace | None:
        return self.by_id

    async def list_active(
        self, *, page: PaginationParams | None
    ) -> Page[SimpleNamespace]:
        return self.active

    async def add(self, row: SimpleNamespace) -> None:
        row.id = 3
        row.public_id = row.public_id or TEMPLATE_ID


class _Versions:
    def __init__(self, session: MagicMock, clinic_id: int | None = None) -> None:
        self.session = session
        self.latest_row: DocumentTemplateVersion | None = _version()
        self.pinned: DocumentTemplateVersion | None = _version()

    async def latest(
        self, *, template_id: int, locale: str
    ) -> DocumentTemplateVersion | None:
        return self.latest_row

    async def get_for_template(
        self, *, template_id: int, version_id: int
    ) -> DocumentTemplateVersion | None:
        return self.pinned

    async def next_version(self, *, template_id: int, locale: str) -> int:
        return 2

    async def list_for_template(
        self, template_id: int
    ) -> list[DocumentTemplateVersion]:
        row = self.latest_row
        return [row] if row is not None else []


class _Documents:
    def __init__(self, session: MagicMock, clinic_id: int | None = None) -> None:
        self.session = session
        self.row: Document | None = _document()
        self.listed = Page(items=[_document()], total=1, limit=25, offset=0)

    async def add(self, row: Document) -> None:
        row.id = 9
        if row.public_id is None:
            row.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FB5"

    async def get_by_public_id(self, public_id: str) -> Document | None:
        return self.row

    async def list_for_patient(
        self, *, patient_id: int, page: PaginationParams | None
    ) -> Page[Document]:
        return self.listed


class _Recipients:
    def __init__(self, session: MagicMock, clinic_id: int | None = None) -> None:
        self.session = session

    async def add(self, row: SimpleNamespace) -> None:
        row.id = 11
        row.public_id = "01ARZ3NDEKTSV4RRFFQ69G5FB7"


class _Patients:
    def __init__(self, session: MagicMock, clinic_id: int | None = None) -> None:
        self.visible: SimpleNamespace | None = _patient()
        self.by_id: SimpleNamespace | None = _patient()

    async def get_visible(
        self, public_id: str, *, created_by_id: int | None
    ) -> SimpleNamespace | None:
        return self.visible

    async def get(self, patient_id: int) -> SimpleNamespace | None:
        return self.by_id


class _Clinics:
    def __init__(self, session: MagicMock) -> None:
        self.row: SimpleNamespace | None = SimpleNamespace(default_locale="en")

    async def get(self, clinic_id: int) -> SimpleNamespace | None:
        return self.row


class _Attachments:
    def __init__(self, session: MagicMock, clinic_id: int | None = None) -> None:
        self.row: SimpleNamespace | None = SimpleNamespace(
            storage_key="documents/one.pdf",
            filename="summary.pdf",
        )

    async def get(self, attachment_id: int) -> SimpleNamespace | None:
        return self.row


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    session = MagicMock()
    session.commit = AsyncMock()
    templates = _Templates(session)
    versions = _Versions(session)
    documents = _Documents(session)
    recipients = _Recipients(session)
    patients = _Patients(session)
    clinics = _Clinics(session)
    attachments = _Attachments(session)
    monkeypatch.setattr(
        "ent.features.documents.service.DocumentTemplateRepository",
        lambda session, clinic_id=None: templates,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.DocumentTemplateVersionRepository",
        lambda session, clinic_id=None: versions,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.DocumentRepository",
        lambda session, clinic_id=None: documents,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.DocumentRecipientRepository",
        lambda session, clinic_id=None: recipients,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.PatientRepository",
        lambda session, clinic_id=None: patients,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.ClinicRepository",
        lambda session: clinics,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.AttachmentRepository",
        lambda session, clinic_id=None: attachments,
    )
    monkeypatch.setattr(
        "ent.features.documents.templates.service.DocumentTemplateRepository",
        lambda session, clinic_id=None: templates,
    )
    monkeypatch.setattr(
        "ent.features.documents.templates.service.DocumentTemplateVersionRepository",
        lambda session, clinic_id=None: versions,
    )
    monkeypatch.setattr(
        "ent.features.documents.templates.service.ClinicRepository",
        lambda session: clinics,
    )
    monkeypatch.setattr(
        "ent.features.documents.service.load_summary_data",
        AsyncMock(return_value={"patient": {"fullName": "ليلى"}}),
    )
    monkeypatch.setattr(
        "ent.features.documents.service.enqueue_job",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "ent.features.documents.service.created_by_scope",
        lambda user: None,
    )
    storage = AsyncMock()
    storage.create_presigned_download.return_value = PresignedUrl(
        url="local-storage://summary.pdf",
        method="GET",
        expires_in_seconds=300,
        headers={},
    )
    monkeypatch.setattr(
        "ent.features.documents.service.get_object_storage",
        lambda settings: storage,
    )
    return SimpleNamespace(
        session=session,
        templates=templates,
        versions=versions,
        documents=documents,
        patients=patients,
        clinics=clinics,
        attachments=attachments,
        storage=storage,
        documents_service=DocumentService(session),
        templates_service=DocumentTemplateService(session),
    )


def _create_body() -> DocumentCreate:
    return DocumentCreate(
        patient_public_id=PATIENT_ID,
        template_code="patient_summary",
        locale="ar",
    )


@pytest.mark.asyncio
async def test_create_list_get_and_finalize_document(world: SimpleNamespace) -> None:
    user = _user()
    created = await world.documents_service.create_document(
        user=user, body=_create_body()
    )
    assert created.status == "draft"
    assert created.title == "ملخص المريض"
    assert created.locale == "ar"

    listed = await world.documents_service.list_documents(
        user=user,
        patient_public_id=PATIENT_ID,
        page_params=PaginationParams(limit=25, offset=0),
    )
    assert listed.page.total == 1
    assert listed.items[0].template_code == "patient_summary"

    fetched = await world.documents_service.get_document(
        user=user, public_id=created.public_id
    )
    assert fetched.patient_public_id == PATIENT_ID

    world.documents.row = _document()
    finalized = await world.documents_service.finalize_document(
        user=user,
        public_id=world.documents.row.public_id,
        body=DocumentFinalize(body_override_html="<p>{{ patient.fullName }}</p>"),
    )
    assert finalized.status == "final"
    assert finalized.content_hash
    world.documents.row.rendered_attachment_id = 8
    download = await world.documents_service.download_url(
        user=user, public_id=world.documents.row.public_id
    )
    assert download.url == "local-storage://summary.pdf"
    recipient = await world.documents_service.add_recipient(
        user=user,
        public_id=world.documents.row.public_id,
        body=DocumentRecipientCreate(
            recipient_type="patient",
            name="ليلى",
            channel="print",
        ),
    )
    assert recipient.delivery_status == "pending"


@pytest.mark.asyncio
async def test_document_guards(world: SimpleNamespace) -> None:
    user = _user()
    service = world.documents_service
    world.patients.visible = None
    with pytest.raises(NotFoundError):
        await service.create_document(user=user, body=_create_body())
    world.patients.visible = _patient()
    world.clinics.row = None
    with pytest.raises(NotFoundError):
        await service.create_document(user=user, body=_create_body())
    world.clinics.row = SimpleNamespace(default_locale="en")
    world.templates.by_code = None
    with pytest.raises(NotFoundError):
        await service.create_document(user=user, body=_create_body())
    world.templates.by_code = _template()
    world.versions.latest_row = None
    with pytest.raises(NotFoundError):
        await service.create_document(user=user, body=_create_body())
    with pytest.raises(ValidationError):
        await service.create_document(
            user=user,
            body=DocumentCreate.model_construct(
                patient_public_id=PATIENT_ID,
                template_code="patient_summary",
                locale="de",
            ),
        )

    world.documents.row = None
    with pytest.raises(NotFoundError):
        await service.get_document(user=user, public_id=PATIENT_ID)
    world.documents.row = _document(status="final")
    with pytest.raises(DocumentImmutableError):
        await service.finalize_document(
            user=user,
            public_id=world.documents.row.public_id,
            body=DocumentFinalize(),
        )
    world.documents.row = _document()
    with pytest.raises(DocumentNotRenderedError):
        await service.download_url(user=user, public_id=world.documents.row.public_id)
    world.documents.row.status = "cancelled"
    with pytest.raises(DocumentImmutableError):
        await service.add_recipient(
            user=user,
            public_id=world.documents.row.public_id,
            body=DocumentRecipientCreate(recipient_type="other", name="Lab"),
        )


@pytest.mark.asyncio
async def test_finalize_rejects_bad_override_and_hidden_rows(
    world: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _user()
    service = world.documents_service
    world.documents.row = _document()
    world.versions.pinned = None
    with pytest.raises(NotFoundError):
        await service.finalize_document(
            user=user,
            public_id=world.documents.row.public_id,
            body=DocumentFinalize(),
        )
    world.versions.pinned = _version()
    with pytest.raises(DocumentTemplateError):
        await service.finalize_document(
            user=user,
            public_id=world.documents.row.public_id,
            body=DocumentFinalize(body_override_html="<p>{{ patient.secret }}</p>"),
        )
    with pytest.raises(DocumentSyntaxError):
        await service.finalize_document(
            user=user,
            public_id=world.documents.row.public_id,
            body=DocumentFinalize(body_override_html="{{"),
        )
    world.patients.by_id = None
    with pytest.raises(NotFoundError):
        await service.get_document(user=user, public_id=world.documents.row.public_id)
    world.patients.by_id = _patient()
    world.templates.by_id = None
    listed = await service.list_documents(
        user=user,
        patient_public_id=PATIENT_ID,
        page_params=PaginationParams(limit=25, offset=0),
    )
    assert listed.items[0].template_code == ""
    world.documents.row.rendered_attachment_id = 8
    world.attachments.row = None
    with pytest.raises(NotFoundError):
        await service.download_url(user=user, public_id=world.documents.row.public_id)
    with pytest.raises(NotFoundError):
        await service.finalize_document(
            user=user,
            public_id=world.documents.row.public_id,
            body=DocumentFinalize(),
        )
    world.patients.by_id = _patient()
    monkeypatch.setattr(
        "ent.features.documents.service.created_by_scope",
        lambda current: 99,
    )
    with pytest.raises(NotFoundError):
        await service.get_document(user=user, public_id=world.documents.row.public_id)


@pytest.mark.asyncio
async def test_template_create_version_and_list(world: SimpleNamespace) -> None:
    user = _user()
    service = world.templates_service
    created = await service.create_template(
        user=user,
        body=DocumentTemplateCreate(
            code="clinic_note",
            category="handout",
            placeholders={"patient.fullName": PlaceholderSpec(type="string")},
        ),
    )
    assert created.code == "clinic_note"
    world.templates.by_code = _template()
    with pytest.raises(ValidationError):
        await service.create_template(
            user=user,
            body=DocumentTemplateCreate(
                code="patient_summary",
                category="patient_summary",
                placeholders={"patient.fullName": PlaceholderSpec(type="string")},
            ),
        )
    with pytest.raises(ValidationError):
        await service.create_template(
            user=user,
            body=DocumentTemplateCreate(
                code="bad_key",
                category="handout",
                placeholders={"1bad": PlaceholderSpec(type="string")},
            ),
        )
    world.templates.by_public = None
    with pytest.raises(NotFoundError):
        await service.add_template_version(
            user=user,
            template_public_id=TEMPLATE_ID,
            body=DocumentTemplateVersionCreate(
                locale="en",
                direction="ltr",
                body_html="<p>{{ patient.fullName }}</p>",
                page_setup=_page_setup(),
            ),
        )
    world.templates.by_public = _template(clinic_id=None)
    with pytest.raises(NotFoundError):
        await service.add_template_version(
            user=user,
            template_public_id=TEMPLATE_ID,
            body=DocumentTemplateVersionCreate(
                locale="en",
                direction="ltr",
                body_html="<p>{{ patient.fullName }}</p>",
                page_setup=_page_setup(),
            ),
        )
    world.templates.by_public = _template()
    with pytest.raises(ValidationError):
        await service.add_template_version(
            user=user,
            template_public_id=TEMPLATE_ID,
            body=DocumentTemplateVersionCreate(
                locale="ar",
                direction="ltr",
                body_html="<p>{{ patient.fullName }}</p>",
                page_setup=_page_setup(),
            ),
        )
    with pytest.raises(DocumentTemplateError):
        await service.add_template_version(
            user=user,
            template_public_id=TEMPLATE_ID,
            body=DocumentTemplateVersionCreate(
                locale="en",
                direction="ltr",
                body_html="<p>{{ patient.secret }}</p>",
                page_setup=_page_setup(),
            ),
        )
    revised = await service.add_template_version(
        user=user,
        template_public_id=TEMPLATE_ID,
        body=DocumentTemplateVersionCreate(
            locale="fr",
            direction="ltr",
            body_html="<p>{{ patient.fullName }}</p>",
            page_setup=_page_setup(),
        ),
    )
    assert revised.public_id == TEMPLATE_ID
    listed = await service.list_templates(
        user=user, page_params=PaginationParams(limit=50, offset=0)
    )
    assert listed.page.total == 1
    detail = await service.get_template(user=user, template_public_id=TEMPLATE_ID)
    assert detail.versions[0].locale == "ar"
    preview = await service.preview(
        user=user,
        body=DocumentTemplatePreview(
            locale="ar",
            direction="rtl",
            body_html="<p>{{ patient.fullName }}</p>",
            placeholders={"patient.fullName": PlaceholderSpec(type="string")},
            page_setup=_page_setup(),
        ),
    )
    assert 'dir="rtl"' in preview.html


@pytest.mark.asyncio
async def test_document_preview_uses_frozen_or_live_html(
    world: SimpleNamespace,
) -> None:
    user = _user()
    drafted = _document()
    world.documents.row = drafted
    live = await world.documents_service.preview_html(
        user=user, public_id=drafted.public_id
    )
    assert "A" in live.html
    drafted.status = "final"
    drafted.content_snapshot = {
        "data": {"patient": {"fullName": "Frozen"}},
        "template": {
            "locale": "en",
            "direction": "ltr",
            "header_html": "",
            "body_html": "<p>{{ patient.fullName }}</p>",
            "footer_html": "",
            "css": "",
            "page_setup": {"title": "Note"},
        },
    }
    frozen = await world.documents_service.preview_html(
        user=user, public_id=drafted.public_id
    )
    assert "Frozen" in frozen.html
