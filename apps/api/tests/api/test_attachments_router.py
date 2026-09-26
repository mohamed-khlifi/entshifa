"""Attachment API smoke tests."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient

from ent.main import create_app
from ent.settings import get_settings
from tests.support.env import clear_settings_cache


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_attachment_upload_confirm_and_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from ent.core.db.session import get_session_factory
    from ent.integrations.storage import get_object_storage
    from tests.support.auth_seed import seed_auth_fixtures

    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path))
    clear_settings_cache()
    app = create_app(settings=get_settings())

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
        token = login.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        upload_resp = await client.post(
            "/api/v1/attachments/upload-url",
            headers=headers,
            json={
                "category": "clinical_photo",
                "filename": "ear.jpg",
                "contentType": "image/jpeg",
                "sizeBytes": 128,
            },
        )
        assert upload_resp.status_code == 200
        body = upload_resp.json()
        upload_token = body["uploadToken"]
        upload_url = body["upload"]["url"]

        parsed = urlparse(upload_url)
        params = parse_qs(parsed.query)
        storage = get_object_storage(get_settings())
        await storage.put_object_bytes(
            key=params["key"][0],
            data=b"\xff\xd8\xff" + b"\x00" * 125,
            content_type="image/jpeg",
        )

        confirm = await client.post(
            "/api/v1/attachments/confirm",
            headers=headers,
            json={"uploadToken": upload_token},
        )
        assert confirm.status_code == 200
        public_id = confirm.json()["publicId"]

        detail = await client.get(
            f"/api/v1/attachments/{public_id}",
            headers=headers,
        )
        assert detail.status_code == 200

        download = await client.get(
            f"/api/v1/attachments/{public_id}/download-url",
            headers=headers,
        )
        assert download.status_code == 200
        assert download.json()["download"]["url"]
