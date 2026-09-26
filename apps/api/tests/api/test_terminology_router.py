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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminology_admin_clinic_override_and_coverage(app) -> None:
    from tests.support.clinic_seed import seed_clinic_admin_fixtures

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
            json={"email": fixtures["admin_email"], "password": fixtures["password"]},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

        created = await client.post(
            "/api/v1/terminology/admin/concepts",
            headers=headers,
            json={
                "code": f"LOCAL.{fixtures['admin_email'].split('+')[1].split('@')[0]}",
                "kind": "finding",
                "locale": "en",
                "display": "Clinic finding",
            },
        )
        assert created.status_code == 201
        public_id = created.json()["publicId"]
        assert created.json()["clinicOwned"] is True

        search = await client.get(
            "/api/v1/terminology/concepts/search",
            headers=headers,
            params={"q": "tympanic", "locale": "en", "kind": "anatomy"},
        )
        assert search.status_code == 200
        anatomy = next(
            item for item in search.json()["items"] if item["code"] == "ANAT.TM"
        )

        override = await client.put(
            f"/api/v1/terminology/admin/concepts/{anatomy['publicId']}/translations/en",
            headers=headers,
            json={"display": "Local tympanic name"},
        )
        assert override.status_code == 200
        assert any(
            row["display"] == "Local tympanic name" and row["clinicOwned"]
            for row in override.json()["translations"]
        )

        member = await client.post(
            "/api/v1/terminology/admin/value-sets/tm.findings/members",
            headers=headers,
            json={"conceptPublicId": public_id, "sortOrder": 9, "isDefault": False},
        )
        assert member.status_code == 201
        assert any(item["publicId"] == public_id for item in member.json()["members"])

        blocked = await client.delete(
            f"/api/v1/terminology/admin/concepts/{public_id}",
            headers=headers,
        )
        assert blocked.status_code == 409
        assert blocked.json()["context"]["reason"] == "concept_in_use"

        deactivated = await client.patch(
            f"/api/v1/terminology/admin/concepts/{public_id}",
            headers=headers,
            json={"isActive": False},
        )
        assert deactivated.status_code == 200
        assert deactivated.json()["isActive"] is False

        coverage = await client.get(
            "/api/v1/terminology/admin/translation-coverage",
            headers=headers,
            params={"locale": "ar", "limit": 50},
        )
        assert coverage.status_code == 200
        assert coverage.json()["page"]["total"] >= 1
        counts = [item["usageCount"] for item in coverage.json()["items"]]
        assert counts == sorted(counts, reverse=True)
