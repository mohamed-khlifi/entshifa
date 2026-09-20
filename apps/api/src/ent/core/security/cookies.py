"""Refresh-token cookie helpers."""

from __future__ import annotations

from fastapi import Response

from ent.settings import Settings

REFRESH_TOKEN_COOKIE = "ent_refresh_token"


def set_refresh_cookie(
    response: Response,
    *,
    settings: Settings,
    raw_token: str,
) -> None:
    secure = settings.app_env != "local"
    max_age = settings.refresh_token_ttl_days * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=raw_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path="/api/v1/auth",
    )
