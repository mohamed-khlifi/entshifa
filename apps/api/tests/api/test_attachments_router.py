"""Attachment API smoke tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ent.main import create_app
from ent.settings import get_settings


@pytest.fixture
def app():
    return create_app(settings=get_settings())


@pytest.mark.asyncio
async def test_upload_url_requires_authentication(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/attachments/upload-url",
            json={
                "category": "clinical_photo",
                "filename": "ear.jpg",
                "contentType": "image/jpeg",
                "sizeBytes": 1024,
            },
        )
    assert response.status_code == 401
    assert response.json()["code"] == "auth.unauthenticated"


@pytest.mark.asyncio
async def test_download_url_requires_authentication(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/attachments/01ARZ3NDEKTSV4RRFFQ69G5FAV/download-url",
        )
    assert response.status_code == 401
