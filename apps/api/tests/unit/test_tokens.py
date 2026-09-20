"""Unit tests for JWT access tokens."""

from __future__ import annotations

from ent.core.security.permissions import Permission
from ent.core.security.tokens import create_access_token, decode_access_token
from ent.settings import get_settings


def test_access_token_round_trip() -> None:
    settings = get_settings()
    token = create_access_token(
        settings=settings,
        user_public_id="01JAAAAAAAAAAAAAAAAAAAAAAA",
        session_public_id="01JBBBBBBBBBBBBBBBBBBBBBB",
        clinic_public_id="01JCCCCCCCCCCCCCCCCCCCCCC",
        permissions=frozenset({Permission.AUTH_SESSION_READ.value}),
    )
    payload = decode_access_token(settings, token)
    assert payload["sub"] == "01JAAAAAAAAAAAAAAAAAAAAAAA"
    assert Permission.AUTH_SESSION_READ.value in payload["perm"]
