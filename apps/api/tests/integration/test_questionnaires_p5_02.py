"""P5-02 launch instrument seed and API scoring."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.db.session import get_session_factory
from ent.main import create_app
from ent.seeds.instruments_launch_specs import LAUNCH_INSTRUMENT_SPECS
from ent.seeds.system import seed_system
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_launch_instruments_seeded_and_localized() -> None:
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

        listed = await client.get(
            "/api/v1/instruments",
            headers=headers,
            params={"limit": 100},
        )
        assert listed.status_code == 200, listed.text
        codes = {row["code"] for row in listed.json()["items"]}
        for launch in LAUNCH_INSTRUMENT_SPECS:
            assert launch.code in codes

        for locale in ("en", "fr", "ar"):
            snot = await client.get(
                "/api/v1/instruments/by-code/snot22",
                headers=headers,
                params={"locale": locale},
            )
            assert snot.status_code == 200, snot.text
            body = snot.json()
            assert body["locale"] == locale
            assert len(body["items"]) == 22
            assert body["title"]

        dhi = await client.get(
            "/api/v1/instruments/by-code/dhi",
            headers=headers,
        )
        assert dhi.status_code == 200, dhi.text
        public_id = dhi.json()["publicId"]
        answers = {f"d{i}": 0 for i in range(1, 26)}
        scored = await client.post(
            f"/api/v1/instruments/{public_id}/score",
            headers=headers,
            json={"answers": answers},
        )
        assert scored.status_code == 200, scored.text
        assert scored.json()["totalScore"] == "0.00"
        assert scored.json()["severityBand"] == "none"
