"""Auth request schemas."""

from __future__ import annotations

from pydantic import Field

from ent.core.schemas.base import CamelModel


class LoginRequest(CamelModel):
    email: str = Field(min_length=3, max_length=190)
    password: str = Field(min_length=8, max_length=128)
