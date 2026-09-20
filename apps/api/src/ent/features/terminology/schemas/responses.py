"""Terminology API schemas."""

from __future__ import annotations

from ent.core.schemas.base import CamelModel, PageSchema


class ResolvedConcept(CamelModel):
    """Concept with locale-resolved display fields."""

    public_id: str
    code: str
    kind: str
    display: str
    full_name: str | None = None
    abbreviation: str | None = None
    patient_friendly: str | None = None
    locale: str
    translation_missing: bool = False
    is_default: bool | None = None
    sort_order: int | None = None


class ConceptSearchResponse(PageSchema[ResolvedConcept]):
    """Paginated concept search results."""


class ValueSetRead(CamelModel):
    code: str
    name_key: str
    description_key: str | None = None
    locale: str
    members: list[ResolvedConcept]


class ConceptDictionaryResponse(CamelModel):
    """Bulk concept map for frontend caching (keyed by publicId)."""

    locale: str
    concepts: dict[str, ResolvedConcept]
