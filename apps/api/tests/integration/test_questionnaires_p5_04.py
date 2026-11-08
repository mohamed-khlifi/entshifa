"""P5-04 questionnaire response presentation fields."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.security.tokens import hash_refresh_token
from ent.features.questionnaires.models import QuestionnaireInvitation
from ent.main import create_app
from ent.seeds.system import seed_system
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_response_detail_includes_items_and_scale_metadata() -> None:
    factory = get_session_factory()
    async with factory() as session:
        try:
            await seed_system(session)
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    app = create_app(settings=get_settings())
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

        created_patient = await client.post(
            "/api/v1/patients",
            headers=headers,
            json={
                "firstName": "Score",
                "lastName": "Present",
                "birthDate": "1985-06-15",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert created_patient.status_code == 201, created_patient.text
        patient_id = created_patient.json()["publicId"]

        invite = await client.post(
            f"/api/v1/patients/{patient_id}/questionnaire-invitations",
            headers=headers,
            json={
                "instrumentCode": "snot22",
                "channel": "tablet",
                "context": "waiting_room",
                "locale": "en",
            },
        )
        assert invite.status_code == 201, invite.text
        token = invite.json()["token"]

        async with factory() as session:
            row = await session.scalar(
                select(QuestionnaireInvitation).where(
                    QuestionnaireInvitation.token_hash == hash_refresh_token(token),
                ),
            )
            assert row is not None

        answers = {f"q{i}": 3 for i in range(1, 23)}
        submit = await client.post(
            f"/api/v1/public/questionnaires/{token}/submit",
            json={"answers": answers},
        )
        assert submit.status_code == 201, submit.text

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/questionnaire-responses",
            headers=headers,
            params={"locale": "en"},
        )
        assert listed.status_code == 200, listed.text
        summary = listed.json()["items"][0]
        assert summary["minScore"] == 0
        assert summary["maxScore"] == 110
        assert summary["mcid"] is not None
        assert summary["totalScore"] is not None
        response_id = summary["publicId"]

        detail = await client.get(
            f"/api/v1/questionnaire-responses/{response_id}",
            headers=headers,
            params={"locale": "en"},
        )
        assert detail.status_code == 200, detail.text
        body = detail.json()
        assert len(body["items"]) == 22
        first = body["items"][0]
        assert first["code"] == "q1"
        assert first["position"] == 1
        assert first["text"]
        assert first["optionText"]
        assert first["value"] == 3
        assert first["minValue"] == 0
        assert first["maxValue"] == 5
        assert first["subscale"] == "rhinologic"
