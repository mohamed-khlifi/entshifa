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


class ConceptCreate(CamelModel):
    code: str = Field(min_length=2, max_length=60)
    kind: str = Field(min_length=2, max_length=40)
    locale: str = Field(min_length=2, max_length=10)
    display: str = Field(min_length=1, max_length=255)
    full_name: str | None = Field(default=None, max_length=400)
    abbreviation: str | None = Field(default=None, max_length=40)
    patient_friendly: str | None = Field(default=None, max_length=400)
    sort_order: int = 0


class ConceptUpdate(CamelModel):
    is_active: bool | None = None
    sort_order: int | None = None


class ConceptTranslationUpsert(CamelModel):
    display: str = Field(min_length=1, max_length=255)
    full_name: str | None = Field(default=None, max_length=400)
    abbreviation: str | None = Field(default=None, max_length=40)
    patient_friendly: str | None = Field(default=None, max_length=400)
    synonyms: list[str] | None = None


class ValueSetMemberCreate(CamelModel):
    concept_public_id: str = Field(min_length=26, max_length=26)
    sort_order: int = 0
    is_default: bool = False


class ValueSetMemberUpdate(CamelModel):
    sort_order: int | None = None
    is_default: bool | None = None
