"""Document API tests (P1-09)."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.features.documents.models import Document
from ent.features.documents.seed import ensure_patient_summary_template
from ent.integrations.storage import get_object_storage
from ent.jobs.tasks.render_document import render_document
from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures
from tests.support.env import clear_settings_cache


def _patient_body() -> dict[str, object]:
    return {
        "firstName": "Leila",
        "lastName": "Ben Salem",
        "firstNameAlt": "ليلى",
        "lastNameAlt": "بن سالم",
        "birthDate": "1975-03-12",
        "sex": "female",
        "preferredLocale": "en",
    }


@pytest.mark.asyncio
async def test_documents_require_authentication() -> None:
    app = create_app(settings=get_settings())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get(
            "/api/v1/documents",
            params={"patientPublicId": "01ARZ3NDEKTSV4RRFFQ69G5FAV"},
        )
        templates = await client.get("/api/v1/document-templates")
    assert listed.status_code == 401
    assert templates.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_summary_finalizes_and_renders_pdf(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path))
    clear_settings_cache()
    app = create_app(settings=get_settings())
    from ent.core.db.session import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await ensure_patient_summary_template(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["admin_email"], "password": fixtures["password"]},
        )
        if admin_login.status_code != 200:
            pytest.skip("Login failed against database")
        admin = {"Authorization": f"Bearer {admin_login.json()['accessToken']}"}
        doctor_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["doctor_email"], "password": fixtures["password"]},
        )
        assert doctor_login.status_code == 200
        doctor = {"Authorization": f"Bearer {doctor_login.json()['accessToken']}"}

        forbidden = await client.post(
            "/api/v1/document-templates",
            headers=doctor,
            json={
                "code": "clinic_note",
                "category": "handout",
                "placeholders": {
                    "patient.fullName": {"type": "string", "required": True}
                },
            },
        )
        assert forbidden.status_code == 403

        created_template = await client.post(
            "/api/v1/document-templates",
            headers=admin,
            json={
                "code": "clinic_note",
                "category": "handout",
                "placeholders": {
                    "patient.fullName": {"type": "string", "required": True}
                },
            },
        )
        assert created_template.status_code == 201, created_template.text
        template_id = created_template.json()["publicId"]

        bad_direction = await client.post(
            f"/api/v1/document-templates/{template_id}/versions",
            headers=admin,
            json={
                "locale": "ar",
                "direction": "ltr",
                "bodyHtml": "<p>{{ patient.fullName }}</p>",
                "pageSetup": {"title": "Note"},
            },
        )
        assert bad_direction.status_code == 422
        assert bad_direction.json()["code"] == "validation_failed"

        undeclared = await client.post(
            f"/api/v1/document-templates/{template_id}/versions",
            headers=admin,
            json={
                "locale": "en",
                "direction": "ltr",
                "bodyHtml": "<p>{{ patient.secret }}</p>",
                "pageSetup": {"title": "Note"},
            },
        )
        assert undeclared.status_code == 422
        assert undeclared.json()["code"] == "documents.undeclared_placeholder"

        patient = await client.post(
            "/api/v1/patients",
            headers={**admin, "Idempotency-Key": "doc-patient-1"},
            json=_patient_body(),
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        drafted = await client.post(
            "/api/v1/documents",
            headers=doctor,
            json={
                "patientPublicId": patient_id,
                "templateCode": "patient_summary",
                "locale": "ar",
            },
        )
        assert drafted.status_code == 201, drafted.text
        document_id = drafted.json()["publicId"]
        assert drafted.json()["status"] == "draft"
        assert drafted.json()["title"] == "ملخص المريض"

        early_download = await client.get(
            f"/api/v1/documents/{document_id}/download-url",
            headers=doctor,
        )
        assert early_download.status_code == 409
        assert early_download.json()["code"] == "documents.not_rendered"

        finalized = await client.post(
            f"/api/v1/documents/{document_id}/finalize",
            headers=doctor,
            json={},
        )
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["status"] == "final"
        assert finalized.json()["contentHash"]

        again = await client.post(
            f"/api/v1/documents/{document_id}/finalize",
            headers=doctor,
            json={},
        )
        assert again.status_code == 409
        assert again.json()["code"] == "documents.immutable"

        recipient = await client.post(
            f"/api/v1/documents/{document_id}/recipients",
            headers=doctor,
            json={
                "recipientType": "patient",
                "name": "ليلى بن سالم",
                "channel": "print",
            },
        )
        assert recipient.status_code == 201

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["admin_email"], "password": fixtures["password"]},
        )
        assert other_login.status_code == 200

    async with factory() as session:
        from ent.features.clinics.models import Clinic
        from ent.seeds.identity import ensure_role, ensure_user_with_role

        stored = (
            await session.execute(
                select(Document).where(Document.public_id == document_id)
            )
        ).scalar_one()
        frozen_body = stored.content_snapshot["template"]["body_html"]
        assert "ملخص المريض" in frozen_body
        other_clinic = (
            await session.execute(
                select(Clinic).where(
                    Clinic.public_id == fixtures["other_clinic_public_id"]
                )
            )
        ).scalar_one()
        other_role = await ensure_role(
            session,
            clinic=other_clinic,
            code="doctor",
            name_key="role.doctor",
        )
        other_doctor = await ensure_user_with_role(
            session,
            clinic=other_clinic,
            role=other_role,
            email=f"other-doc+{document_id[:8].lower()}@test.entshifa.local",
            first_name="Other",
            last_name="Doctor",
            password=fixtures["password"],
        )
        await session.commit()
        other_email = other_doctor.email

    rendered = await render_document(document_public_id=document_id)
    assert rendered["ok"] is True
    storage = get_object_storage(get_settings())
    async with factory() as session:
        stored = (
            await session.execute(
                select(Document).where(Document.public_id == document_id)
            )
        ).scalar_one()
        from ent.features.attachments.models import Attachment

        attachment = await session.get(Attachment, stored.rendered_attachment_id)
        assert attachment is not None
        payload = await storage.get_object_bytes(key=attachment.storage_key)
    assert payload.startswith(b"%PDF")
    assert len(payload) > 1000

    repeated = await render_document(document_public_id=document_id)
    assert repeated["skipped"] is True

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doctor_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["doctor_email"], "password": fixtures["password"]},
        )
        doctor = {"Authorization": f"Bearer {doctor_login.json()['accessToken']}"}
        download = await client.get(
            f"/api/v1/documents/{document_id}/download-url",
            headers=doctor,
        )
        assert download.status_code == 200, download.text
        assert download.json()["url"]

        missing = await client.get(
            "/api/v1/documents/01ARZ3NDEKTSV4RRFFQ69G5FAV",
            headers=doctor,
        )
        assert missing.status_code == 404

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200
        other = {"Authorization": f"Bearer {other_login.json()['accessToken']}"}
        hidden = await client.get(
            f"/api/v1/documents/{document_id}",
            headers=other,
        )
        assert hidden.status_code == 404
