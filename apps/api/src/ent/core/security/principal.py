"""Authenticated principal attached to each request."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: int
    user_public_id: str
    session_id: int
    session_public_id: str
    clinic_id: int
    clinic_public_id: str
    permissions: frozenset[str]
