"""Auth response schemas."""

from __future__ import annotations

from ent.core.schemas.base import CamelModel


class SessionResponse(CamelModel):
    user_public_id: str
    clinic_public_id: str
    session_public_id: str


class LoginResponse(CamelModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in_minutes: int = 0
    session: SessionResponse | None = None
    mfa_required: bool = False
    mfa_token: str | None = None


class MeResponse(CamelModel):
    user_public_id: str
    clinic_public_id: str
    permissions: list[str]
