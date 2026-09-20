"""Terminology API contract tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.db.session import get_session_factory
from ent.main import create_app
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.auth_seed import seed_auth_fixtures


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_terminology_requires_auth(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/terminology/dictionary")
    assert response.status_code == 401
    assert response.json()["code"] == "auth.unauthenticated"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminology_endpoints_for_authenticated_user(app) -> None:
    factory = get_session_factory()
    async with factory() as session:
        fixtures = await seed_auth_fixtures(session)
        await seed_terminology(session)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["email"], "password": fixtures["password"]},
        )
        assert login.status_code == 200
        token = login.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        search = await client.get(
            "/api/v1/terminology/concepts/search",
            params={"q": "tympanic", "locale": "en", "kind": "anatomy"},
            headers=headers,
        )
        assert search.status_code == 200
        body = search.json()
        assert "items" in body
        assert body["page"]["limit"] <= 100
        assert any(item["code"] == "ANAT.TM" for item in body["items"])

        value_set = await client.get(
            "/api/v1/terminology/value-sets/tm.findings",
            params={"locale": "fr"},
            headers=headers,
        )
        assert value_set.status_code == 200
        vs = value_set.json()
        assert vs["code"] == "tm.findings"
        assert len(vs["members"]) == 4

        dictionary = await client.get(
            "/api/v1/terminology/dictionary",
            params={"locale": "en", "kinds": "anatomy,finding"},
            headers=headers,
        )
        assert dictionary.status_code == 200
        concepts = dictionary.json()["concepts"]
        assert len(concepts) >= 10

        missing = await client.get(
            "/api/v1/terminology/value-sets/does.not.exist",
            headers=headers,
        )
        assert missing.status_code == 404
        assert missing.json()["code"] == "not_found"
