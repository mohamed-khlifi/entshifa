"""API tests for clinics, sites and clinical settings (P1-01)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_clinic_requires_authentication(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/clinic")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clinic_sites_and_settings_flow() -> None:
    from ent.core.db.session import get_session_factory

    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
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

        clinic = await client.get("/api/v1/clinic", headers=doctor_headers)
        assert clinic.status_code == 200
        assert clinic.json()["publicId"] == fixtures["clinic_public_id"]

        forbidden = await client.patch(
            "/api/v1/clinic",
            headers=doctor_headers,
            json={"name": "Should Fail"},
        )
        assert forbidden.status_code == 403

        patched = await client.patch(
            "/api/v1/clinic",
            headers=admin_headers,
            json={"name": "Renamed Clinic", "city": "Lyon"},
        )
        assert patched.status_code == 200
        assert patched.json()["name"] == "Renamed Clinic"
        assert patched.json()["city"] == "Lyon"

        sites = await client.get("/api/v1/sites", headers=admin_headers)
        assert sites.status_code == 200
        assert sites.json()["page"]["total"] >= 1

        created = await client.post(
            "/api/v1/sites",
            headers=admin_headers,
            json={"name": "Annexe Test", "city": "Villeurbanne", "isPrimary": False},
        )
        assert created.status_code == 201
        site_id = created.json()["publicId"]
        assert created.json()["isPrimary"] is False

        # Cross-tenant: other clinic's site returns 404, not 403
        cross = await client.get(
            f"/api/v1/sites/{fixtures['other_site_public_id']}",
            headers=admin_headers,
        )
        assert cross.status_code == 404

        settings = await client.get(
            "/api/v1/settings/clinical",
            headers=doctor_headers,
        )
        assert settings.status_code == 200
        keys = {item["key"] for item in settings.json()["items"]}
        assert "pta_formula" in keys
        assert all(item["source"] == "system" for item in settings.json()["items"])

        put = await client.put(
            "/api/v1/settings/clinical",
            headers=admin_headers,
            json={"items": [{"key": "pta_formula", "value": "3freq"}]},
        )
        assert put.status_code == 200
        pta = next(i for i in put.json()["items"] if i["key"] == "pta_formula")
        assert pta["value"] == "3freq"
        assert pta["source"] == "clinic"

        doctor_forbidden_settings = await client.put(
            "/api/v1/settings/clinical",
            headers=doctor_headers,
            json={"items": [{"key": "pta_formula", "value": "fletcher"}]},
        )
        assert doctor_forbidden_settings.status_code == 403

        deleted = await client.delete(
            f"/api/v1/sites/{site_id}",
            headers=admin_headers,
        )
        assert deleted.status_code == 204

        gone = await client.get(f"/api/v1/sites/{site_id}", headers=admin_headers)
        assert gone.status_code == 404
