"""Terminology use cases."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError
from ent.core.schemas.base import PageMeta
from ent.core.security.principal import CurrentUser
from ent.features.clinics.models import Clinic
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository
from ent.features.terminology.schemas.responses import (
    ConceptDictionaryResponse,
    ConceptSearchResponse,
    ResolvedConcept,
    ValueSetRead,
)


class TerminologyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_concepts(
        self,
        *,
        user: CurrentUser,
        q: str,
        locale: str | None,
        kind: str | None,
        limit: int,
        offset: int,
    ) -> ConceptSearchResponse:
        clinic = await self._clinic(user.clinic_id)
        resolved_locale = locale or clinic.default_locale
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concepts, total = await repo.search_concepts(
            query=q,
            kind=kind,
            limit=limit,
            offset=offset,
        )
        items = await self._resolve_many(
            repo,
            concepts,
            locale=resolved_locale,
            clinic_default_locale=clinic.default_locale,
        )
        return ConceptSearchResponse(
            items=items,
            page=PageMeta(total=total, limit=limit, offset=offset),
        )

    async def get_value_set(
        self,
        *,
        user: CurrentUser,
        code: str,
        locale: str | None,
    ) -> ValueSetRead:
        clinic = await self._clinic(user.clinic_id)
        resolved_locale = locale or clinic.default_locale
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        value_set = await repo.get_value_set_by_code(code)
        if value_set is None:
            raise NotFoundError(resource="value_set", code=code)

        members = await repo.list_value_set_members(value_set.id)
        ordered = [
            m.concept
            for m in members
            if m.concept is not None and m.concept.deleted_at is None and m.concept.is_active
        ]
        resolved = await self._resolve_many(
            repo,
            ordered,
            locale=resolved_locale,
            clinic_default_locale=clinic.default_locale,
        )
        member_meta = {m.concept_id: m for m in members}
        for item, concept in zip(resolved, ordered, strict=True):
            meta = member_meta.get(concept.id)
            if meta is not None:
                item.is_default = meta.is_default
                item.sort_order = meta.sort_order

        return ValueSetRead(
            code=value_set.code,
            name_key=value_set.name_key,
            description_key=value_set.description_key,
            locale=resolved_locale,
            members=resolved,
        )

    async def get_dictionary(
        self,
        *,
        user: CurrentUser,
        locale: str | None,
        kinds: list[str] | None,
    ) -> ConceptDictionaryResponse:
        clinic = await self._clinic(user.clinic_id)
        resolved_locale = locale or clinic.default_locale
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concepts = await repo.list_concepts_by_kinds(kinds)
        resolved = await self._resolve_many(
            repo,
            concepts,
            locale=resolved_locale,
            clinic_default_locale=clinic.default_locale,
        )
        return ConceptDictionaryResponse(
            locale=resolved_locale,
            concepts={item.public_id: item for item in resolved},
        )

    async def _clinic(self, clinic_id: int) -> Clinic:
        result = await self._session.execute(select(Clinic).where(Clinic.id == clinic_id))
        clinic = result.scalar_one_or_none()
        if clinic is None:
            raise NotFoundError(resource="clinic")
        return clinic

    async def _resolve_many(
        self,
        repo: TerminologyRepository,
        concepts: list[Concept],
        *,
        locale: str,
        clinic_default_locale: str,
    ) -> list[ResolvedConcept]:
        translations = await repo.load_translations_for_concepts([c.id for c in concepts])
        items: list[ResolvedConcept] = []
        for concept in concepts:
            display = repo.resolve_display(
                concept=concept,
                translations=translations.get(concept.id, []),
                locale=locale,
                clinic_default_locale=clinic_default_locale,
            )
            items.append(
                ResolvedConcept(
                    public_id=concept.public_id,
                    code=concept.code,
                    kind=concept.kind,
                    display=display.display,
                    full_name=display.full_name,
                    abbreviation=display.abbreviation,
                    patient_friendly=display.patient_friendly,
                    locale=display.locale,
                    translation_missing=display.translation_missing,
                ),
            )
        return items
