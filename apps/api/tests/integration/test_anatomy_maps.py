"""P2-04 map terminology and narrative rendering against seeded concepts."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.main import create_app
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_map_value_sets_and_narrative_order() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await seed_terminology(session)
            await session.commit()
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
        headers = {
            "Authorization": f"Bearer {login.json()['accessToken']}",
            "Accept-Language": "en",
        }
        value_set = await client.get(
            "/api/v1/terminology/value-sets/oral.tonsil.findings",
            headers=headers,
            params={"locale": "en"},
        )
        assert value_set.status_code == 200, value_set.text
        codes = {member["code"] for member in value_set.json()["members"]}
        assert "FIND.TONSIL.BRODSKY_4" in codes
        assert "FIND.TONSIL.NORMAL" in codes

        rendered = await client.post(
            "/api/v1/narrative/render",
            headers=headers,
            json={
                "findings": [
                    {
                        "conceptCode": "FIND.TM.NORMAL",
                        "bodySiteCode": "ANAT.TM.PT.AS",
                        "mapRegionCode": "tm.pars-tensa.antero-superior",
                        "laterality": "left",
                        "status": "normal",
                        "sortIndex": 1,
                    },
                    {
                        "conceptCode": "FIND.TM.PERFORATION",
                        "bodySiteCode": "ANAT.TM.PT.AI",
                        "mapRegionCode": "tm.pars-tensa.antero-inferior",
                        "laterality": "right",
                        "status": "abnormal",
                        "sortIndex": 3,
                    },
                    {
                        "conceptCode": "FIND.CANAL.NORMAL",
                        "bodySiteCode": "ANAT.EAR.CANAL",
                        "mapRegionCode": "tm.canal",
                        "laterality": "right",
                        "status": "not_examined",
                        "sortIndex": 0,
                    },
                ]
            },
        )
        assert rendered.status_code == 200, rendered.text
        body = rendered.json()
        assert body["locale"] == "en"
        assert body["text"] == (
            "Right\n"
            "Anteroinferior quadrant: perforation\n"
            "\n"
            "Left\n"
            "Anterosuperior quadrant: normal"
        )

        created = await client.post(
            "/api/v1/patients",
            headers=headers,
            json={
                "firstName": "Map",
                "lastName": f"Exam{new_ulid()[:6]}",
                "birthDate": "1990-01-01",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert created.status_code == 201, created.text
        patient_id = created.json()["publicId"]
        recorded = await client.post(
            f"/api/v1/observations/patient/{patient_id}/batch",
            headers=headers,
            json={
                "encounterPublicId": new_ulid(),
                "observations": [
                    {
                        "conceptCode": "FIND.TONSIL.BRODSKY_2",
                        "bodySiteCode": "ANAT.ORAL.TONSIL",
                        "mapRegionCode": "oral.tonsil",
                        "laterality": "right",
                        "status": "abnormal",
                        "valueType": "code",
                        "valueConceptCode": "FIND.TONSIL.BRODSKY_2",
                        "effectiveAt": "2026-06-01T09:00:00",
                        "source": "clinician",
                        "confirmed": True,
                    }
                ],
            },
        )
        assert recorded.status_code == 201, recorded.text
        row = recorded.json()[0]
        assert row["mapRegionCode"] == "oral.tonsil"
        assert row["bodySite"]["code"] == "ANAT.ORAL.TONSIL"
        assert row["laterality"] == "right"
        assert row["concept"]["code"] == "FIND.TONSIL.BRODSKY_2"
