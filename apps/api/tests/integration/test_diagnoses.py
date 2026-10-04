"""P2-07 diagnoses: coded rows, promotion, lock, copy-forward, favourites."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.terminology.models import Concept
from ent.main import create_app
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_diagnosis_is_a_concept_and_promotes_to_the_problem_list() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await seed_terminology(session)
            diagnosis = (
                await session.execute(
                    select(Concept).where(
                        Concept.code == "H60.9", Concept.deleted_at.is_(None)
                    )
                )
            ).scalar_one()
            anatomy = (
                await session.execute(
                    select(Concept).where(
                        Concept.code == "ANAT.EAR", Concept.deleted_at.is_(None)
                    )
                )
            ).scalar_one()
            await session.commit()
            diagnosis_id = diagnosis.public_id
            anatomy_id = anatomy.public_id
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

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
        created_patient = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Ear",
                "lastName": f"Dx{suffix}",
                "birthDate": "1978-04-04",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert created_patient.status_code == 201, created_patient.text
        patient_id = created_patient.json()["publicId"]
        created = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json={
                "patientPublicId": patient_id,
                "sitePublicId": site_id,
                "encounterType": "consultation",
                "startedAt": "2026-06-02T09:00:00",
                "complaints": [
                    {
                        "conceptCode": "CC.EAR_PAIN",
                        "laterality": "right",
                        "sortOrder": 0,
                        "isPrimary": True,
                    }
                ],
            },
        )
        assert created.status_code == 201, created.text
        encounter_id = created.json()["publicId"]
        version = created.json()["version"]

        rejected = await client.patch(
            f"/api/v1/encounters/{encounter_id}",
            headers=headers,
            json={
                "version": version,
                "diagnoses": [
                    {
                        "conceptPublicId": anatomy_id,
                        "laterality": "right",
                        "status": "suspected",
                    }
                ],
            },
        )
        assert rejected.status_code == 422, rejected.text
        assert rejected.json()["code"] == "diagnosis.invalid_concept"

        saved = await client.patch(
            f"/api/v1/encounters/{encounter_id}",
            headers=headers,
            json={
                "version": version,
                "diagnoses": [
                    {
                        "conceptPublicId": diagnosis_id,
                        "laterality": "right",
                        "status": "confirmed",
                        "sortOrder": 0,
                    }
                ],
            },
        )
        assert saved.status_code == 200, saved.text
        rows = saved.json()["diagnoses"]
        assert len(rows) == 1
        assert rows[0]["concept"]["code"] == "H60.9"
        assert rows[0]["status"] == "confirmed"
        assert rows[0]["laterality"] == "right"
        assert rows[0]["isPrimary"] is True
        diagnosis_public_id = rows[0]["publicId"]
        version = saved.json()["version"]

        promoted = await client.post(
            f"/api/v1/encounters/{encounter_id}/diagnoses/{diagnosis_public_id}/promote",
            headers=headers,
        )
        assert promoted.status_code == 200, promoted.text
        assert promoted.json()["promotedProblemPublicId"]
        again = await client.post(
            f"/api/v1/encounters/{encounter_id}/diagnoses/{diagnosis_public_id}/promote",
            headers=headers,
        )
        assert again.status_code == 200, again.text
        assert (
            again.json()["promotedProblemPublicId"]
            == promoted.json()["promotedProblemPublicId"]
        )

        chart = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
        assert chart.status_code == 200, chart.text
        problems = chart.json()["problems"]
        assert len(problems) == 1
        assert problems[0]["status"] == "active"
        assert problems[0]["diagnosis"]["code"] == "H60.9"

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/problems", headers=headers
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["items"][0]["status"] == "active"

        signed = await client.post(
            f"/api/v1/encounters/{encounter_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        locked = await client.patch(
            f"/api/v1/encounters/{encounter_id}",
            headers=headers,
            json={
                "version": signed.json()["version"],
                "diagnoses": [
                    {
                        "conceptPublicId": diagnosis_id,
                        "laterality": "left",
                        "status": "suspected",
                    }
                ],
            },
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "encounter.already_signed"

        copied = await client.post(
            f"/api/v1/encounters/{encounter_id}/copy-forward",
            headers=headers,
            json={"startedAt": "2026-07-01T09:00:00"},
        )
        assert copied.status_code == 201, copied.text
        cloned = copied.json()["diagnoses"]
        assert len(cloned) == 1
        assert cloned[0]["source"] == "copy_forward"
        assert cloned[0]["concept"]["code"] == "H60.9"
        assert cloned[0]["derivedFromPublicId"] == diagnosis_public_id

        favorites = await client.put(
            "/api/v1/diagnoses/favorites",
            headers=headers,
            json={"conceptPublicIds": [diagnosis_id]},
        )
        assert favorites.status_code == 200, favorites.text
        assert favorites.json()["items"][0]["concept"]["code"] == "H60.9"
        listed_favorites = await client.get(
            "/api/v1/diagnoses/favorites", headers=headers
        )
        assert listed_favorites.status_code == 200
        assert (
            listed_favorites.json()["items"][0]["concept"]["conceptId"] == diagnosis_id
        )
