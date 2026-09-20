from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from ent.features.health.dependencies import get_health_service_for_request
from ent.features.health.schemas.responses import (
    LiveHealthResponse,
    ReadinessCheck,
    ReadyHealthResponse,
)
from ent.features.health.service import HealthService
from ent.main import create_app
from ent.settings import get_settings


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_health_live_returns_200(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "live"}


@pytest.mark.asyncio
async def test_health_ready_returns_503_when_dependency_fails(app) -> None:
    mock_service = MagicMock(spec=HealthService)
    mock_service.ready = AsyncMock(
        return_value=(
            ReadyHealthResponse(
                status="not_ready",
                checks=[
                    ReadinessCheck(name="mysql", status="error"),
                    ReadinessCheck(name="redis", status="ok"),
                    ReadinessCheck(name="storage", status="ok"),
                ],
            ),
            False,
        ),
    )
    app.dependency_overrides[get_health_service_for_request] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"][0]["name"] == "mysql"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_ready_all_dependencies_when_stack_running(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
    if response.status_code == 503:
        pytest.skip("Docker stack not running or bucket not initialized")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
