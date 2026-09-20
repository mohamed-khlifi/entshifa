"""Terminology request query helpers."""

from __future__ import annotations

from pydantic import Field

from ent.core.schemas.base import CamelModel


class ConceptSearchParams(CamelModel):
    q: str = Field(min_length=1, max_length=120)
    locale: str | None = Field(default=None, max_length=10)
    kind: str | None = Field(default=None, max_length=40)
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
