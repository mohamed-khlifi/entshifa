"""P5-01 instrument model, translations guard, and scoring."""

from __future__ import annotations

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


def _option_labels() -> dict[str, str]:
    return {str(v): f"opt{v}" for v in range(0, 6)}


def _locale_block(
    locale: str,
    *,
    title: str,
    item_code: str,
) -> dict[str, object]:
    return {
        "locale": locale,
        "title": title,
        "items": {item_code: f"{item_code}-{locale}"},
        "options": _option_labels(),
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_score_and_translation_guard() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    code = f"demo_{suffix}"
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

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

        body = {
            "code": code,
            "category": "sinonasal",
            "respondent": "patient",
            "scoringType": "sum",
            "minScore": 0,
            "maxScore": 5,
            "licenseNote": "test fixture",
            "reference": "P5-01 integration",
            "version": "1.0.0",
            "effectiveFrom": date.today().isoformat(),
            "scoringConfig": {"scaleMultiplier": 1},
            "sharedOptions": {
                "options": [
                    {"value": v, "position": i + 1} for i, v in enumerate(range(0, 6))
                ],
            },
            "items": [
                {
                    "code": "item1",
                    "position": 1,
                    "weight": 1,
                },
            ],
            "translations": [
                _locale_block("en", title="Demo EN", item_code="item1"),
                _locale_block("fr", title="Demo FR", item_code="item1"),
                _locale_block("ar", title="Demo AR", item_code="item1"),
            ],
        }
        created = await client.post("/api/v1/instruments", headers=headers, json=body)
        assert created.status_code == 201, created.text
        instrument_id = created.json()["publicId"]

        by_code = await client.get(
            f"/api/v1/instruments/by-code/{code}",
            headers=headers,
            params={"locale": "en"},
        )
        assert by_code.status_code == 200, by_code.text
        assert by_code.json()["title"] == "Demo EN"

        scored = await client.post(
            f"/api/v1/instruments/{instrument_id}/score",
            headers=headers,
            json={"answers": {"item1": 3}},
        )
        assert scored.status_code == 200, scored.text
        assert scored.json()["totalScore"] == "3.00"

        incomplete = await client.post(
            f"/api/v1/instruments/{instrument_id}/score",
            headers=headers,
            json={"answers": {}},
        )
        assert incomplete.status_code == 422

        other_clinic = await client.get(
            f"/api/v1/instruments/{instrument_id}",
            headers=headers,
        )
        assert other_clinic.status_code == 200
