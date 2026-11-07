"""P5-03 questionnaire invitation and public patient flow."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.security.tokens import hash_refresh_token
from ent.features.questionnaires.models import QuestionnaireInvitation
from ent.integrations.email import get_email_outbox
from ent.integrations.messaging import get_messaging_outbox
from ent.main import create_app
from ent.seeds.system import seed_system
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tablet_invitation_public_flow_and_single_use() -> None:
    get_email_outbox().clear()
    get_messaging_outbox().clear()
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
                "firstName": "Question",
                "lastName": "Patient",
                "birthDate": "1990-01-01",
                "sex": "female",
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
        assert token

        async with factory() as session:
            row = await session.scalar(
                select(QuestionnaireInvitation).where(
                    QuestionnaireInvitation.token_hash == hash_refresh_token(token),
                ),
            )
            assert row is not None
            assert row.token_hash != token

        public_get = await client.get(f"/api/v1/public/questionnaires/{token}")
        assert public_get.status_code == 200, public_get.text
        body = public_get.json()
        assert body["patientFirstName"] == "Question"
        assert "lastName" not in body
        assert "publicId" not in body
        assert len(body["instrument"]["items"]) == 22

        answers = {f"q{i}": 0 for i in range(1, 23)}
        submit = await client.post(
            f"/api/v1/public/questionnaires/{token}/submit",
            json={"answers": answers},
        )
        assert submit.status_code == 201, submit.text

        again = await client.get(f"/api/v1/public/questionnaires/{token}")
        assert again.status_code == 409
        assert again.json()["code"] == "questionnaire.invitation_already_completed"

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/questionnaire-responses",
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["items"][0]["enteredBy"] == "patient"
