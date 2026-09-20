"""Auth response schemas."""

from __future__ import annotations

from ent.core.schemas.base import CamelModel


class SessionResponse(CamelModel):
    user_public_id: str
    clinic_public_id: str
    session_public_id: str


class LoginResponse(CamelModel):
    access_token: str
    token_type: str
    expires_in_minutes: int
    session: SessionResponse


class MeResponse(CamelModel):
    user_public_id: str
    clinic_public_id: str
    permissions: list[str]
