"""P4-06 hearing devices, pediatric screening and OME integration tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.patients.models import PatientFlag
from ent.features.recalls.models import Recall
from ent.main import create_app
from ent.seeds.identity import LOCAL_DEV_PASSWORD, ensure_role, ensure_user_with_role
from ent.seeds.protocols import seed_protocols
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_p4_06_hearing_device_ome_and_ehdi() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    tech_email = f"audio-p406-{suffix}@test.entshifa.local"
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
            await seed_protocols(session)
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
                last_name="P406",
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
                "firstName": "Ped",
                "lastName": f"P406{suffix}",
                "birthDate": "2025-06-01",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        screening = await client.put(
            f"/api/v1/patients/{patient_id}/audiology/pediatric/screening",
            headers=tech_headers,
            json={
                "screenDate": "2025-07-01",
                "screenResultRight": "refer",
                "screenResultLeft": "pass",
                "diagnosticAbrDate": "2025-08-15",
                "diagnosticAbrResultRight": "elevated",
                "permanentHearingLoss": True,
            },
        )
        assert screening.status_code == 200, screening.text
        body = screening.json()
        assert body["screenBy1MStatus"] == "met"
        assert body["diagnosisBy3MStatus"] == "met"

        ome = await client.post(
            "/api/v1/ome-episodes",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "laterality": "bilateral",
                "firstSeenOn": "2026-01-10",
                "hearingLevelDb": 30,
            },
        )
        assert ome.status_code == 201, ome.text
        assert ome.json()["watchfulWaitingDueOn"] == "2026-04-10"

        async with factory() as session:
            recalls = list(
                (
                    await session.scalars(
                        select(Recall).where(
                            Recall.reason_key == "audiology_ome_watchful_waiting",
                            Recall.deleted_at.is_(None),
                        )
                    )
                ).all()
            )
            assert recalls

        device = await client.post(
            "/api/v1/hearing-devices",
            headers={**tech_headers, "Idempotency-Key": new_ulid()},
            json={
                "patientPublicId": patient_id,
                "ear": "right",
                "deviceType": "cochlear_implant",
                "fittedOn": "2026-02-01",
                "status": "active",
            },
        )
        assert device.status_code == 201, device.text

        async with factory() as session:
            flags = list(
                (
                    await session.scalars(
                        select(PatientFlag).where(
                            PatientFlag.flag_code == "cochlear_implant",
                            PatientFlag.deleted_at.is_(None),
                            PatientFlag.ended_on.is_(None),
                        )
                    )
                ).all()
            )
            assert flags
