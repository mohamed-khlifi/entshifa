"""API tests for the patient registry (P1-05)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.features.clinics.models import Clinic
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_BIRTH = "1980-04-02"


def _patient_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "firstName": "Bén",
        "lastName": "Alï",
        "firstNameAlt": "بن",
        "lastNameAlt": "علي",
        "birthDate": _BIRTH,
        "sex": "male",
        "preferredLocale": "fr",
        "phonePrimary": "+216 12 345 678",
    }
    body.update(overrides)
    return body


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_patients_require_authentication(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/patients")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_registry_acceptance() -> None:
    from ent.core.db.session import get_session_factory

    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            other = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["other_clinic_public_id"]
                    )
                )
            ).scalar_one()
            other_role = await ensure_role(
                session,
                clinic=other,
                code="clinic_admin",
                name_key="role.clinic_admin",
            )
            other_admin = await ensure_user_with_role(
                session,
                clinic=other,
                role=other_role,
                email=f"other-admin+{fixtures['clinic_public_id'][:8]}@test.entshifa.local",
                first_name="Other",
                last_name="Admin",
                password=fixtures["password"],
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
            pytest.skip("Login failed against database")
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['accessToken']}"}

        doctor_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["doctor_email"], "password": fixtures["password"]},
        )
        assert doctor_login.status_code == 200
        doctor_headers = {
            "Authorization": f"Bearer {doctor_login.json()['accessToken']}"
        }

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_admin.email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200
        other_headers = {"Authorization": f"Bearer {other_login.json()['accessToken']}"}

        created = await client.post(
            "/api/v1/patients",
            headers={**admin_headers, "Idempotency-Key": "patient-create-1"},
            json=_patient_body(
                flags=[
                    {
                        "flagCode": "only_hearing_ear",
                        "laterality": "left",
                        "startedOn": "2020-01-15",
                        "isAuto": False,
                    }
                ]
            ),
        )
        assert created.status_code == 201, created.text
        patient = created.json()
        patient_id = patient["publicId"]
        assert patient["firstNameAlt"] == "بن"
        assert patient["flags"][0]["flagCode"] == "only_hearing_ear"
        assert patient["flags"][0]["startedOn"] == "2020-01-15"
        assert patient["flags"][0]["recordedByPublicId"]
        assert patient["phonePrimary"] == "21612345678"

        replay = await client.post(
            "/api/v1/patients",
            headers={**admin_headers, "Idempotency-Key": "patient-create-1"},
            json=_patient_body(
                flags=[
                    {
                        "flagCode": "only_hearing_ear",
                        "laterality": "left",
                        "startedOn": "2020-01-15",
                        "isAuto": False,
                    }
                ]
            ),
        )
        assert replay.status_code == 201
        assert replay.json()["publicId"] == patient_id

        latin = await client.get(
            "/api/v1/patients",
            headers=admin_headers,
            params={"search": "Ben Ali"},
        )
        assert latin.status_code == 200
        latin_ids = [item["publicId"] for item in latin.json()["items"]]
        assert patient_id in latin_ids
        matched = next(
            item for item in latin.json()["items"] if item["publicId"] == patient_id
        )
        assert matched["firstNameAlt"] == "بن"
        assert matched["lastNameAlt"] == "علي"

        arabic = await client.get(
            "/api/v1/patients",
            headers=admin_headers,
            params={"search": "بن علي"},
        )
        assert patient_id in [item["publicId"] for item in arabic.json()["items"]]

        by_phone = await client.get(
            "/api/v1/patients",
            headers=admin_headers,
            params={"search": "21612345678"},
        )
        assert patient_id in [item["publicId"] for item in by_phone.json()["items"]]

        by_birth = await client.get(
            "/api/v1/patients",
            headers=admin_headers,
            params={"search": _BIRTH},
        )
        assert patient_id in [item["publicId"] for item in by_birth.json()["items"]]

        flagged = await client.get(
            "/api/v1/patients",
            headers=admin_headers,
            params={"flagCode": "only_hearing_ear"},
        )
        assert patient_id in [item["publicId"] for item in flagged.json()["items"]]

        duplicate = await client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=_patient_body(firstName="Ben", lastName="Ali", phonePrimary=None),
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "patient.possible_duplicate"
        assert patient_id in duplicate.json()["context"]["candidates"]

        phone_duplicate = await client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=_patient_body(
                firstName="Other",
                lastName="Person",
                birthDate="1991-02-03",
                firstNameAlt=None,
                lastNameAlt=None,
                phonePrimary="21612345678",
            ),
        )
        assert phone_duplicate.status_code == 409

        confirmed = await client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=_patient_body(
                firstName="Other",
                lastName="Person",
                birthDate="1992-02-03",
                firstNameAlt=None,
                lastNameAlt=None,
                phonePrimary="+33199999999",
                confirmDuplicate=False,
            ),
        )
        assert confirmed.status_code == 201, confirmed.text
        second_id = confirmed.json()["publicId"]

        hidden = await client.get(
            f"/api/v1/patients/{patient_id}", headers=other_headers
        )
        assert hidden.status_code == 404

        forbidden_merge = await client.post(
            f"/api/v1/patients/{patient_id}/merge",
            headers=doctor_headers,
            json={"mergedPatientId": second_id, "reason": "duplicate chart"},
        )
        assert forbidden_merge.status_code == 403

        merged = await client.post(
            f"/api/v1/patients/{patient_id}/merge",
            headers=admin_headers,
            json={"mergedPatientId": second_id, "reason": "duplicate chart"},
        )
        assert merged.status_code == 200, merged.text
        assert merged.json()["survivingPatientId"] == patient_id

        gone = await client.get(f"/api/v1/patients/{second_id}", headers=admin_headers)
        assert gone.status_code == 404

        stale = await client.patch(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
            json={"version": 99, "city": "Tunis"},
        )
        assert stale.status_code == 409
        assert stale.json()["code"] == "patient.version_conflict"

        technician_denied = await client.post(
            "/api/v1/patients",
            headers=doctor_headers,
            json=_patient_body(
                firstName="New",
                lastName="Chart",
                birthDate="1970-01-01",
                phonePrimary=None,
                firstNameAlt=None,
                lastNameAlt=None,
            ),
        )
        assert technician_denied.status_code == 201
