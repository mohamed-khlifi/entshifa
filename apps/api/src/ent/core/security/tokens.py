"""JWT access tokens and opaque refresh token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from ent.settings import Settings


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def create_access_token(
    *,
    settings: Settings,
    user_public_id: str,
    session_public_id: str,
    clinic_public_id: str,
    permissions: frozenset[str],
) -> str:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": user_public_id,
        "sid": session_public_id,
        "cid": clinic_public_id,
        "perm": sorted(permissions),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.access_token_secret,
        algorithm="HS256",
    )


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.access_token_secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    return payload
