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


class ConceptTranslationRead(CamelModel):
    locale: str
    display: str
    full_name: str | None = None
    abbreviation: str | None = None
    patient_friendly: str | None = None
    synonyms: list[str] | None = None
    clinic_owned: bool


class ConceptAdminRead(CamelModel):
    public_id: str
    code: str
    kind: str
    is_active: bool
    clinic_owned: bool
    sort_order: int
    translations: list[ConceptTranslationRead]


class TranslationCoverageItem(CamelModel):
    public_id: str
    code: str
    kind: str
    usage_count: int
    display: str


class ValueSetSummaryRead(CamelModel):
    code: str
    name_key: str
    description_key: str | None = None
