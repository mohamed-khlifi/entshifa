"""P4-01 audiogram entry API."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.main import create_app
from ent.seeds.identity import LOCAL_DEV_PASSWORD, ensure_role, ensure_user_with_role
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audiogram_entry_finalize_and_recall_closure() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    tech_email = f"audio-tech-{suffix}@test.entshifa.local"
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
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
                last_name="Tech",
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
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['accessToken']}"}

        tech_login = await client.post(
            "/api/v1/auth/login",
            json={"email": tech_email, "password": fixtures["password"]},
        )
        assert tech_login.status_code == 200, tech_login.text
        tech_headers = {"Authorization": f"Bearer {tech_login.json()['accessToken']}"}

        patient = await client.post(
            "/api/v1/patients",
            headers={**admin_headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Hear",
                "lastName": f"Test{suffix}",
                "birthDate": "1990-01-01",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        recall = await client.post(
            "/api/v1/recalls",
            headers={**admin_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientId": patient_id,
                "reasonText": "Audiogram due",
                "reasonLocale": "en",
                "dueOn": "2026-08-01",
                "actionType": "test",
                "actionConfig": {"test": "audiogram"},
            },
        )
        assert recall.status_code == 201, recall.text
        recall_id = recall.json()["publicId"]

        create = await client.post(
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
                        "ear": "right",
                        "conduction": "bone",
                        "frequencyHz": 1000,
                        "levelDb": 10,
                        "isMasked": True,
                    },
                    {
                        "ear": "left",
                        "conduction": "air",
                        "frequencyHz": 4000,
                        "levelDb": 120,
                        "isNoResponse": True,
                    },
                    {
                        "ear": "right",
                        "conduction": "air",
                        "frequencyHz": 12500,
                        "levelDb": 15,
                    },
                ],
            },
        )
        assert create.status_code == 201, create.text
        audiogram_id = create.json()["publicId"]
        assert create.json()["status"] == "draft"
        assert create.json()["hasExtendedHighFrequencies"] is True
        assert len(create.json()["thresholds"]) == 4

        interpret_forbidden = await client.post(
            f"/api/v1/audiograms/{audiogram_id}/interpret",
            headers=tech_headers,
            json={"version": 1, "interpretationText": "secret"},
        )
        assert interpret_forbidden.status_code == 403, interpret_forbidden.text

        finalize = await client.post(
            f"/api/v1/audiograms/{audiogram_id}/finalize",
            headers=tech_headers,
            json={"version": 1},
        )
        assert finalize.status_code == 200, finalize.text
        assert finalize.json()["status"] == "final"
        assert finalize.json()["ptaFormula"] == "4freq_who"
        assert finalize.json()["engineVersion"] == "1.0.0"

        locked = await client.put(
            f"/api/v1/audiograms/{audiogram_id}",
            headers=tech_headers,
            json={"version": 2, "thresholds": []},
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "audiology.already_finalized"

        recall_read = await client.get(
            f"/api/v1/recalls/{recall_id}",
            headers=admin_headers,
        )
        assert recall_read.status_code == 200, recall_read.text
        assert recall_read.json()["status"] == "done"

        interpret = await client.post(
            f"/api/v1/audiograms/{audiogram_id}/interpret",
            headers=admin_headers,
            json={"version": 2, "interpretationText": "Stable thresholds."},
        )
        assert interpret.status_code == 200, interpret.text
        assert interpret.json()["interpretationText"] == "Stable thresholds."
