"""P4-03 speech, tympanometry and ABR integration tests."""

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
async def test_p4_03_tympanometry_jerger_speech_and_recall() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    tech_email = f"audio-p403-{suffix}@test.entshifa.local"
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
                last_name="P403",
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
                "firstName": "P403",
                "lastName": f"Patient{suffix}",
                "birthDate": "1985-06-01",
                "sex": "male",
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
                "reasonText": "Tympanogram due",
                "reasonLocale": "en",
                "dueOn": "2026-09-01",
                "actionType": "test",
                "actionConfig": {"test": "tympanometry"},
            },
        )
        assert recall.status_code == 201, recall.text
        recall_id = recall.json()["publicId"]

        audiogram = await client.post(
            "/api/v1/audiograms",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "performedAt": datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC).isoformat(),
                "thresholds": [
                    {
                        "ear": "right",
                        "conduction": "air",
                        "frequencyHz": 500,
                        "levelDb": 20,
                    },
                    {
                        "ear": "right",
                        "conduction": "air",
                        "frequencyHz": 1000,
                        "levelDb": 20,
                    },
                    {
                        "ear": "right",
                        "conduction": "air",
                        "frequencyHz": 2000,
                        "levelDb": 20,
                    },
                    {
                        "ear": "right",
                        "conduction": "air",
                        "frequencyHz": 4000,
                        "levelDb": 20,
                    },
                ],
            },
        )
        assert audiogram.status_code == 201, audiogram.text
        audiogram_id = audiogram.json()["publicId"]

        speech = await client.post(
            "/api/v1/speech-audiometry",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "audiogramPublicId": audiogram_id,
                "ear": "right",
                "srtDb": 35,
                "wrsPercent": 92,
            },
        )
        assert speech.status_code == 201, speech.text
        assert speech.json()["speechPtaDiscrepancyFlag"] is True

        tymp = await client.post(
            "/api/v1/tympanograms",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "ear": "right",
                "ecvMl": "2.50",
                "complianceMl": "0.15",
                "peakPressureDapa": 0,
            },
        )
        assert tymp.status_code == 201, tymp.text
        assert tymp.json()["suggestedJergerType"] == "B"
        assert tymp.json()["largeCanalVolumeFlag"] is True
        tymp_id = tymp.json()["publicId"]

        interpret = await client.post(
            f"/api/v1/tympanograms/{tymp_id}/interpret",
            headers=admin_headers,
            json={"version": 1, "jergerType": "B"},
        )
        assert interpret.status_code == 200, interpret.text
        assert interpret.json()["jergerTypeIsOverridden"] is True

        abr = await client.post(
            "/api/v1/abr-results",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "ear": "right",
                "stimulus": "click",
                "waveIMs": "1.50",
                "waveIiiMs": "3.80",
                "waveVMs": "5.90",
                "contralateralWaveVMs": "5.50",
            },
        )
        assert abr.status_code == 201, abr.text
        assert abr.json()["interauralVFlag"] is True

        recall_read = await client.get(
            f"/api/v1/recalls/{recall_id}",
            headers=admin_headers,
        )
        assert recall_read.status_code == 200, recall_read.text
        assert recall_read.json()["status"] == "done"
