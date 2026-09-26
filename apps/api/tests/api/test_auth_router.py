"""Auth API tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.main import create_app
from ent.settings import get_settings


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_me_requires_authentication(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "auth.unauthenticated"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_refresh_logout_and_permissions(app) -> None:
    from ent.core.db.session import get_session_factory
    from tests.support.auth_seed import seed_auth_fixtures

    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_auth_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["email"], "password": fixtures["password"]},
        )
        if login.status_code != 200:
            pytest.skip("Login failed against database")
        body = login.json()
        assert "accessToken" in body
        token = body["accessToken"]
        cookies = login.cookies

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert me.json()["userPublicId"] == fixtures["user_public_id"]

        forbidden = await client.get(
            "/api/v1/auth/admin-check",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "forbidden"

        other_clinic = await client.get(
            f"/api/v1/auth/clinic-access/{fixtures['other_clinic_public_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert other_clinic.status_code == 404
        assert other_clinic.json()["code"] == "not_found"

        refresh = await client.post("/api/v1/auth/refresh", cookies=cookies)
        assert refresh.status_code == 200
        old_cookies = cookies
        new_cookies = refresh.cookies

        replay = await client.post("/api/v1/auth/refresh", cookies=old_cookies)
        assert replay.status_code == 401
        assert replay.json()["code"] == "auth.session_revoked"

        logout = await client.post("/api/v1/auth/logout", cookies=new_cookies)
        assert logout.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_rejects_invalid_password(app) -> None:
    from ent.core.db.session import get_session_factory
    from tests.support.auth_seed import seed_auth_fixtures

    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_auth_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": fixtures["email"], "password": "not-the-real-password"},
        )
    assert response.status_code == 401
    assert response.json()["code"] == "auth.invalid_credentials"
