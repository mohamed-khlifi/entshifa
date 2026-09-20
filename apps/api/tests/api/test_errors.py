"""Error handler and RFC 7807 contract tests."""

from __future__ import annotations

from fastapi import APIRouter

from httpx import ASGITransport, AsyncClient
import pytest

from ent.core.errors.exceptions import NotFoundError
from ent.main import create_app
from ent.settings import get_settings


@pytest.fixture
def app():
    application = create_app(settings=get_settings())
    router = APIRouter()

    @router.get("/_test/not-found")
    async def boom() -> None:
        raise NotFoundError(resource="patient")

    @router.get("/_test/crash")
    async def crash() -> None:
        raise RuntimeError("secret internals")

    application.include_router(router)
    return application


@pytest.mark.asyncio
async def test_domain_error_is_problem_json(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/_test/not-found")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["detail"] is None
    assert body["context"] == {"resource": "patient"}
    assert "requestId" in body
    assert len(body["requestId"]) == 26
    assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_validation_error_uses_stable_code(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "x", "password": "short"},
        )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_failed"
    assert "fields" in body["context"]
    assert body["detail"] is None


@pytest.mark.asyncio
async def test_unhandled_error_hides_internals(app) -> None:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/_test/crash")
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error"
    assert body["detail"] is None
    assert "secret" not in response.text
