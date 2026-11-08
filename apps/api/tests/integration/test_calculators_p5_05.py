"""P5-05 calculator registry HTTP integration."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.db.session import get_session_factory
from ent.main import create_app
from ent.seeds.system import seed_system
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calculator_list_get_and_evaluate() -> None:
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

        listing = await client.get("/api/v1/calculators", headers=headers)
        assert listing.status_code == 200, listing.text
        payload = listing.json()
        assert payload["page"]["total"] >= 15
        codes = {item["code"] for item in payload["items"]}
        assert "endoscopy.lund_kennedy" in codes
        assert "audiology.pta" in codes

        spec = await client.get(
            "/api/v1/calculators/endoscopy.lund_kennedy",
            headers=headers,
        )
        assert spec.status_code == 200, spec.text
        assert spec.json()["interactive"] is True
        assert len(spec.json()["inputs"]) == 10

        evaluate = await client.post(
            "/api/v1/calculators/endoscopy.adenoid_obstruction",
            headers=headers,
            json={"inputs": {"percent": 45}},
        )
        assert evaluate.status_code == 200, evaluate.text
        body = evaluate.json()
        assert body["value"] == "45"
        assert body["code"] == "endoscopy.adenoid_obstruction"
