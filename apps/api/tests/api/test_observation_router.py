"""Observation API authentication."""

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
async def test_observation_reads_require_authentication(app) -> None:
    transport = ASGITransport(app=app)
    encounter_id = new_ulid()
    patient_id = new_ulid()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get(f"/api/v1/observations/encounter/{encounter_id}")
        cohort = await client.get(
            "/api/v1/observations/cohort",
            params={
                "conceptCode": "FIND.TM.NORMAL",
                "ordinal": 3,
                "effectiveFrom": "2026-01-01T00:00:00",
                "effectiveTo": "2027-01-01T00:00:00",
            },
        )
        timeline = await client.get(
            f"/api/v1/observations/patient/{patient_id}/concept/FIND.TM.NORMAL/timeline"
        )
    assert listed.status_code == 401
    assert listed.json()["code"] == "auth.unauthenticated"
    assert cohort.status_code == 401
    assert timeline.status_code == 401
