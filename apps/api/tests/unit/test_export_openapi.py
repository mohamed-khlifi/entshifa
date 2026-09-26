"""OpenAPI export produces a committed-shape document with auth schemas."""

from __future__ import annotations

import json
from pathlib import Path

from ent.cli.export_openapi import export_openapi


def test_export_openapi_includes_auth_schemas(tmp_path: Path) -> None:
    out = tmp_path / "openapi.json"
    export_openapi(out)
    document = json.loads(out.read_text(encoding="utf-8"))
    schemas = document["components"]["schemas"]
    assert "LoginRequest" in schemas
    assert "LoginResponse" in schemas
    assert "MeResponse" in schemas
    assert "SessionResponse" in schemas
    # Wire JSON is camelCase (CamelModel aliases).
    login_props = schemas["LoginResponse"]["properties"]
    assert "accessToken" in login_props
    assert "expiresInMinutes" in login_props
    paths = document["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
