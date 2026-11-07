"""P4-07 audiology report document and technician isolation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.documents.seed import ensure_clinical_templates
from ent.main import create_app
from ent.seeds.identity import LOCAL_DEV_PASSWORD, ensure_role, ensure_user_with_role
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audiology_report_and_technician_isolation() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    tech_email = f"audio-p407-{suffix}@test.entshifa.local"
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await ensure_clinical_templates(session)
            clinic = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["clinic_public_id"]
                    )
                )
            ).scalar_one()
            tech_role = await ensure_role(
                session,
                clinic=clinic,
                code="audiology_technician",
                name_key="role.audiology_technician",
            )
            await ensure_user_with_role(
                session,
                clinic=clinic,
                role=tech_role,
                email=tech_email,
                first_name="Audio",
                last_name="P407",
                password=LOCAL_DEV_PASSWORD,
            )
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
            pytest.skip("Login failed")
        doctor_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["doctor_email"], "password": fixtures["password"]},
        )
        assert doctor_login.status_code == 200, doctor_login.text
        doctor_headers = {
            "Authorization": f"Bearer {doctor_login.json()['accessToken']}"
        }
        tech_login = await client.post(
            "/api/v1/auth/login",
            json={"email": tech_email, "password": fixtures["password"]},
        )
        assert tech_login.status_code == 200, tech_login.text
        tech_headers = {"Authorization": f"Bearer {tech_login.json()['accessToken']}"}

        patient = await client.post(
            "/api/v1/patients",
            headers={**doctor_headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Audio",
                "lastName": f"P407{suffix}",
                "birthDate": "1988-04-03",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        audiogram = await client.post(
            "/api/v1/audiograms",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "performedAt": datetime(2026, 6, 10, 9, 0, 0, tzinfo=UTC).isoformat(),
                "thresholds": [
                    {
                        "ear": "right",
                        "conduction": "air",
                        "frequencyHz": 1000,
                        "levelDb": 25,
                    },
                    {
                        "ear": "left",
                        "conduction": "air",
                        "frequencyHz": 1000,
                        "levelDb": 35,
                    },
                ],
            },
        )
        assert audiogram.status_code == 201, audiogram.text
        audiogram_id = audiogram.json()["publicId"]
        await client.post(
            f"/api/v1/audiograms/{audiogram_id}/finalize",
            headers=tech_headers,
            json={"version": 1},
        )
        await client.post(
            f"/api/v1/audiograms/{audiogram_id}/interpret",
            headers=doctor_headers,
            json={"version": 2, "interpretationText": "Mild bilateral loss."},
        )

        doc = await client.post(
            "/api/v1/documents",
            headers={**doctor_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "templateCode": "audiology_report",
                "audiology": {
                    "audiogramPublicId": audiogram_id,
                    "conclusion": "Mild bilateral loss.",
                },
            },
        )
        assert doc.status_code == 201, doc.text
        document_id = doc.json()["publicId"]
        assert doc.json()["category"] == "audiology_report"

        preview = await client.get(
            f"/api/v1/documents/{document_id}/preview",
            headers=doctor_headers,
        )
        assert preview.status_code == 200, preview.text
        assert "data:image/svg+xml;base64," in preview.json()["html"]

        finalized = await client.post(
            f"/api/v1/documents/{document_id}/finalize",
            headers=doctor_headers,
            json={},
        )
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["status"] == "final"
        content_hash = finalized.json()["contentHash"]
        assert content_hash

        tech_doc = await client.post(
            "/api/v1/documents",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "templateCode": "audiology_report",
                "audiology": {"audiogramPublicId": audiogram_id},
            },
        )
        assert tech_doc.status_code == 403, tech_doc.text

        sites = await client.get("/api/v1/sites", headers=doctor_headers)
        assert sites.status_code == 200, sites.text
        site_id = sites.json()["items"][0]["publicId"]
        encounter = await client.post(
            "/api/v1/encounters",
            headers={**doctor_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "sitePublicId": site_id,
                "encounterType": "consultation",
                "startedAt": "2026-06-02T09:00:00",
                "complaints": [],
            },
        )
        assert encounter.status_code == 201, encounter.text
        encounter_id = encounter.json()["publicId"]
        tech_note = await client.get(
            f"/api/v1/encounters/{encounter_id}",
            headers=tech_headers,
        )
        assert tech_note.status_code == 403, tech_note.text

        timeline = await client.get(
            f"/api/v1/patients/{patient_id}/timeline",
            headers=tech_headers,
        )
        assert timeline.status_code == 200, timeline.text
        types = {item["eventType"] for item in timeline.json()["items"]}
        assert "consultation" not in types
        assert "diagnosis" not in types
        assert "prescription" not in types
        assert "document" not in types
