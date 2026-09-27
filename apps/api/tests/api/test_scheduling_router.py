"""API tests for scheduling (P1-07)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_scheduling_requires_authentication(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/appointment-types")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scheduling_acceptance() -> None:
    from ent.core.db.session import get_session_factory

    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["admin_email"], "password": fixtures["password"]},
        )
        if login.status_code != 200:
            pytest.skip("Login failed against database")
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

        types_resp = await client.get("/api/v1/appointment-types", headers=headers)
        assert types_resp.status_code == 200
        if types_resp.json()["items"]:
            type_id = types_resp.json()["items"][0]["publicId"]
        else:
            created_type = await client.post(
                "/api/v1/appointment-types",
                headers=headers,
                json={
                    "code": "test_slot",
                    "nameKey": "scheduling.appointment_type.follow_up",
                    "defaultDurationMin": 20,
                    "color": "#2563eb",
                    "requiresRoom": False,
                },
            )
            assert created_type.status_code == 201
            type_id = created_type.json()["publicId"]

        patients = await client.get("/api/v1/patients?limit=1", headers=headers)
        assert patients.status_code == 200
        patient_items = patients.json()["items"]
        if not patient_items:
            created = await client.post(
                "/api/v1/patients",
                headers=headers,
                json={
                    "firstName": "Sched",
                    "lastName": "Test",
                    "birthDate": "1990-01-01",
                    "sex": "female",
                    "preferredLocale": "en",
                },
            )
            assert created.status_code == 201
            patient_id = created.json()["publicId"]
        else:
            patient_id = patient_items[0]["publicId"]

        sites = await client.get("/api/v1/sites", headers=headers)
        assert sites.status_code == 200
        site_id = sites.json()["items"][0]["publicId"]
        doctor_id = fixtures["doctor_public_id"]

        start = datetime.now(UTC).replace(
            minute=0, second=0, microsecond=0
        ) + timedelta(
            days=1,
            hours=9,
        )
        end = start + timedelta(minutes=30)
        body = {
            "siteId": site_id,
            "patientId": patient_id,
            "userId": doctor_id,
            "appointmentTypeId": type_id,
            "startsAt": start.isoformat().replace("+00:00", "Z"),
            "endsAt": end.isoformat().replace("+00:00", "Z"),
        }
        first = await client.post("/api/v1/appointments", headers=headers, json=body)
        assert first.status_code == 201
        appt_id = first.json()["publicId"]

        overlap_body = {
            **body,
            "startsAt": (start + timedelta(minutes=15))
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            ),
            "endsAt": (end + timedelta(minutes=15)).isoformat().replace("+00:00", "Z"),
        }
        second = await client.post(
            "/api/v1/appointments",
            headers=headers,
            json=overlap_body,
        )
        assert second.status_code == 201
        assert second.json()["overlapWarnings"]

        arrive = await client.post(
            f"/api/v1/appointments/{appt_id}/arrive",
            headers=headers,
        )
        assert arrive.status_code == 200
        assert arrive.json()["status"] == "arrived"

        from sqlalchemy import select

        from ent.core.db.session import get_session_factory
        from ent.features.clinics.models import Clinic
        from ent.seeds.identity import ensure_role, ensure_user_with_role

        factory = get_session_factory()
        async with factory() as session:
            other = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["other_clinic_public_id"],
                    ),
                )
            ).scalar_one()
            other_role = await ensure_role(
                session,
                clinic=other,
                code="clinic_admin",
                name_key="role.clinic_admin",
            )
            other_email = (
                f"sched-other+{fixtures['clinic_public_id'][:8]}@test.entshifa.local"
            )
            await ensure_user_with_role(
                session,
                clinic=other,
                role=other_role,
                email=other_email,
                first_name="Other",
                last_name="Sched",
                password=fixtures["password"],
            )
            await session.commit()

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200
        other_headers = {
            "Authorization": f"Bearer {other_login.json()['accessToken']}",
        }
        cross = await client.get(
            f"/api/v1/appointments/{appt_id}",
            headers=other_headers,
        )
        assert cross.status_code == 404
