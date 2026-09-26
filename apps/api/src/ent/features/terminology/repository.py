"""Terminology repository: queries and locale-aware display resolution."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ColumnElement, Select, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ent.features.terminology.models import (
    Concept,
    ConceptTranslation,
    ValueSet,
    ValueSetMember,
)


@dataclass(frozen=True, slots=True)
class ResolvedDisplay:
    display: str
    full_name: str | None
    abbreviation: str | None
    patient_friendly: str | None
    locale: str
    translation_missing: bool


class TerminologyRepository:
    """Reads global + clinic-scoped terminology; never bypasses soft-delete."""

    def __init__(self, session: AsyncSession, clinic_id: int | None = None) -> None:
        self.session = session
        self.clinic_id = clinic_id

    def _visible_concepts(self) -> Select[tuple[Concept]]:
        stmt = select(Concept).where(
            Concept.deleted_at.is_(None),
            Concept.is_active.is_(True),
        )
        if self.clinic_id is not None:
            stmt = stmt.where(
                or_(Concept.clinic_id.is_(None), Concept.clinic_id == self.clinic_id),
            )
        else:
            stmt = stmt.where(Concept.clinic_id.is_(None))
        return stmt

    async def get_concept_by_public_id(self, public_id: str) -> Concept | None:
        result = await self.session.execute(
            self._visible_concepts().where(Concept.public_id == public_id),
        )
        return result.scalar_one_or_none()

    async def get_concept_by_code(self, code: str) -> Concept | None:
        result = await self.session.execute(
            self._visible_concepts().where(Concept.code == code),
        )
        return result.scalar_one_or_none()

    async def list_concepts_by_kinds(self, kinds: list[str] | None) -> list[Concept]:
        stmt = self._visible_concepts().order_by(
            Concept.kind, Concept.sort_order, Concept.code
        )
        if kinds:
            stmt = stmt.where(Concept.kind.in_(kinds))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_value_set_by_code(self, code: str) -> ValueSet | None:
        result = await self.session.execute(
            select(ValueSet).where(
                ValueSet.code == code,
                ValueSet.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def list_value_set_members(self, value_set_id: int) -> list[ValueSetMember]:
        visibility: ColumnElement[bool] = ValueSetMember.clinic_id.is_(None)
        if self.clinic_id is not None:
            visibility = or_(
                ValueSetMember.clinic_id.is_(None),
                ValueSetMember.clinic_id == self.clinic_id,
            )
        result = await self.session.execute(
            select(ValueSetMember)
            .where(
                ValueSetMember.value_set_id == value_set_id,
                ValueSetMember.deleted_at.is_(None),
                visibility,
            )
            .options(selectinload(ValueSetMember.concept))
            .order_by(ValueSetMember.sort_order, ValueSetMember.id),
        )
        return list(result.scalars().all())

    async def search_concepts(
        self,
        *,
        query: str,
        kind: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Concept], int]:
        term = query.strip()
        if not term:
            return [], 0

        base = self._visible_concepts()
        if kind:
            base = base.where(Concept.kind == kind)

        # Accent/case folding comes from utf8mb4_0900_ai_ci on translation columns.
        like = f"%{term}%"
        match_clause = or_(
            ConceptTranslation.display.like(like),
            ConceptTranslation.full_name.like(like),
            Concept.code.like(like),
            text(
                "JSON_SEARCH(concept_translation.synonyms, 'one', :syn, NULL, '$[*]') "
                "IS NOT NULL",
            ).bindparams(syn=term),
        )

        # Prefer FULLTEXT when the token is long enough for InnoDB (default min 3).
        if len(term) >= 3:
            match_clause = or_(
                match_clause,
                text(
                    "MATCH(concept_translation.display, concept_translation.full_name) "
                    "AGAINST (:ft IN BOOLEAN MODE)",
                ).bindparams(ft=f"{term}*"),
            )

        translation_visibility: ColumnElement[bool] = ConceptTranslation.clinic_id.is_(
            None
        )
        if self.clinic_id is not None:
            translation_visibility = or_(
                ConceptTranslation.clinic_id.is_(None),
                ConceptTranslation.clinic_id == self.clinic_id,
            )

        filtered = (
            base.join(
                ConceptTranslation,
                and_(
                    ConceptTranslation.concept_id == Concept.id,
                    ConceptTranslation.deleted_at.is_(None),
                    translation_visibility,
                ),
            )
            .where(match_clause)
            .distinct()
        )

        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.order_by(None).subquery()),
            )
        ).scalar_one()

        rows = (
            (
                await self.session.execute(
                    filtered.order_by(Concept.kind, Concept.sort_order, Concept.code)
                    .offset(offset)
                    .limit(limit),
                )
            )
            .scalars()
            .all()
        )
        return list(rows), int(total)

    async def load_translations_for_concepts(
        self,
        concept_ids: list[int],
    ) -> dict[int, list[ConceptTranslation]]:
        if not concept_ids:
            return {}
        visibility: ColumnElement[bool] = ConceptTranslation.clinic_id.is_(None)
        if self.clinic_id is not None:
            visibility = or_(
                ConceptTranslation.clinic_id.is_(None),
                ConceptTranslation.clinic_id == self.clinic_id,
            )
        result = await self.session.execute(
            select(ConceptTranslation).where(
                ConceptTranslation.concept_id.in_(concept_ids),
                ConceptTranslation.deleted_at.is_(None),
                visibility,
            ),
        )
        grouped: dict[int, list[ConceptTranslation]] = {cid: [] for cid in concept_ids}
        for row in result.scalars().all():
            grouped.setdefault(row.concept_id, []).append(row)
        return grouped

    def resolve_display(
        self,
        *,
        concept: Concept,
        translations: list[ConceptTranslation],
        locale: str,
        clinic_default_locale: str,
    ) -> ResolvedDisplay:
        """Architecture §20 resolution order."""

        def pick(
            wanted_locale: str, clinic_only: bool | None
        ) -> ConceptTranslation | None:
            candidates = [t for t in translations if t.locale == wanted_locale]
            if clinic_only is True:
                candidates = [t for t in candidates if t.clinic_id == self.clinic_id]
            elif clinic_only is False:
                candidates = [t for t in candidates if t.clinic_id is None]
            # Prefer clinic override when both exist and clinic_only is None.
            if clinic_only is None and self.clinic_id is not None:
                override = next(
                    (t for t in candidates if t.clinic_id == self.clinic_id), None
                )
                if override is not None:
                    return override
                return next((t for t in candidates if t.clinic_id is None), None)
            return candidates[0] if candidates else None

        chosen = (
            pick(locale, True)
            or pick(locale, False)
            or pick(clinic_default_locale, True)
            or pick(clinic_default_locale, False)
            or pick(locale, None)
            or pick(clinic_default_locale, None)
        )
        if chosen is None:
            return ResolvedDisplay(
                display=concept.code,
                full_name=None,
                abbreviation=None,
                patient_friendly=None,
                locale=locale,
                translation_missing=True,
            )
        return ResolvedDisplay(
            display=chosen.display,
            full_name=chosen.full_name,
            abbreviation=chosen.abbreviation,
            patient_friendly=chosen.patient_friendly,
            locale=chosen.locale,
            translation_missing=False,
        )
