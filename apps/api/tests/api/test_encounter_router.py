"""Encounter API authentication."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.utils.ids import new_ulid
from ent.main import create_app
from ent.settings import get_settings


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_encounter_reads_require_authentication(app) -> None:
    transport = ASGITransport(app=app)
    encounter_id = new_ulid()
    patient_id = new_ulid()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get(f"/api/v1/patients/{patient_id}/encounters")
        loaded = await client.get(f"/api/v1/encounters/{encounter_id}")
    assert listed.status_code == 401
    assert listed.json()["code"] == "auth.unauthenticated"
    assert loaded.status_code == 401
