"""P2-11 manual recalls and the patient timeline."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.recalls.dates import clinic_local_date, due_on_from_interval
from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_manual_recall_books_an_appointment_and_appears_on_the_timeline() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    expected_due = due_on_from_interval(
        clinic_local_date(datetime.now(UTC), "Europe/Paris"), 42
    ).isoformat()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": fixtures["admin_email"],
                "password": fixtures["password"],
            },
        )
        if login.status_code != 200:
            pytest.skip("Login failed against database")
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        sites = await client.get("/api/v1/sites", headers=headers)
        assert sites.status_code == 200, sites.text
        site_id = sites.json()["items"][0]["publicId"]
        created_type = await client.post(
            "/api/v1/appointment-types",
            headers=headers,
            json={
                "code": f"fu-{suffix}",
                "nameKey": "scheduling.appointment_type.follow_up",
                "defaultDurationMin": 20,
                "color": "#0f766e",
                "requiresRoom": False,
            },
        )
        assert created_type.status_code == 201, created_type.text
        type_id = created_type.json()["publicId"]
        created_patient = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Follow",
                "lastName": f"Up{suffix}",
                "birthDate": "1984-02-02",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert created_patient.status_code == 201, created_patient.text
        patient_id = created_patient.json()["publicId"]
        created_encounter = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json={
                "patientPublicId": patient_id,
                "sitePublicId": site_id,
                "encounterType": "consultation",
                "startedAt": "2026-06-02T09:00:00",
                "chiefComplaintSummary": "nasal obstruction",
            },
        )
        assert created_encounter.status_code == 201, created_encounter.text
        encounter_id = created_encounter.json()["publicId"]
        payload = {
            "patientId": patient_id,
            "reasonText": "See in 6 weeks with an audiogram",
            "reasonLocale": "en",
            "intervalDays": 42,
            "windowDays": 14,
            "actionType": "test",
            "actionConfig": {"test": "audiogram"},
            "sourceEncounterId": encounter_id,
            "appointment": {
                "siteId": site_id,
                "userId": fixtures["doctor_public_id"],
                "appointmentTypeId": type_id,
                "startsAt": "2026-12-01T09:00:00Z",
            },
        }
        key = new_ulid()
        created = await client.post(
            "/api/v1/recalls",
            headers={**headers, "Idempotency-Key": key},
            json=payload,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["dueOn"] == expected_due
        assert body["status"] == "booked"
        assert body["actionConfig"]["test"] == "audiogram"
        assert body["appointmentId"]
        assert body["sourceEncounterId"] == encounter_id
        replay = await client.post(
            "/api/v1/recalls",
            headers={**headers, "Idempotency-Key": key},
            json=payload,
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["publicId"] == body["publicId"]

        listed = await client.get(
            "/api/v1/recalls",
            headers=headers,
            params={"patientId": patient_id, "bucket": "active", "limit": 25},
        )
        assert listed.status_code == 200, listed.text
        assert any(
            item["publicId"] == body["publicId"] for item in listed.json()["items"]
        )

        called = await client.post(
            f"/api/v1/recalls/{body['publicId']}/actions",
            headers=headers,
            json={"action": "call", "outcome": "no_answer", "version": body["version"]},
        )
        assert called.status_code == 200, called.text
        assert called.json()["attempts"] == 1
        unreachable = await client.post(
            f"/api/v1/recalls/{body['publicId']}/actions",
            headers=headers,
            json={
                "action": "call",
                "outcome": "unreachable",
                "version": called.json()["version"],
            },
        )
        assert unreachable.status_code == 200, unreachable.text
        assert unreachable.json()["status"] == "unreachable"
        assert unreachable.json()["attempts"] == 2

        summary = await client.get("/api/v1/recalls/summary", headers=headers)
        assert summary.status_code == 200, summary.text
        assert summary.json()["unreachable"] >= 1

        timeline = await client.get(
            f"/api/v1/patients/{patient_id}/timeline",
            headers=headers,
            params={"limit": 50},
        )
        assert timeline.status_code == 200, timeline.text
        kinds = {item["eventType"] for item in timeline.json()["items"]}
        assert "consultation" in kinds
        assert "recall" in kinds
        assert "appointment" in kinds

        foreign = await client.get(
            f"/api/v1/recalls/{new_ulid()}",
            headers=headers,
        )
        assert foreign.status_code == 404
