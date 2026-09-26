"""Terminology use cases."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError
from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.terminology.models import (
    CONCEPT_KINDS,
    Concept,
    ConceptTranslation,
    ValueSetMember,
)
from ent.features.terminology.repository import TerminologyRepository
from ent.features.terminology.schemas.requests import (
    ConceptCreate,
    ConceptTranslationUpsert,
    ConceptUpdate,
    ValueSetMemberCreate,
    ValueSetMemberUpdate,
)
from ent.features.terminology.schemas.responses import (
    ConceptAdminRead,
    ConceptDictionaryResponse,
    ConceptSearchResponse,
    ConceptTranslationRead,
    ResolvedConcept,
    TranslationCoverageItem,
    ValueSetRead,
    ValueSetSummaryRead,
)


class TerminologyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

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
            if m.concept is not None
            and m.concept.deleted_at is None
            and m.concept.is_active
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

    async def list_admin_concepts(
        self,
        *,
        user: CurrentUser,
        q: str | None,
        kind: str | None,
        clinic_owned_only: bool,
        limit: int,
        offset: int,
    ) -> PageSchema[ConceptAdminRead]:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        rows, total = await repo.list_admin_concepts(
            q=q,
            kind=kind,
            clinic_owned_only=clinic_owned_only,
            limit=limit,
            offset=offset,
        )
        items = await self._admin_reads(repo, rows)
        return PageSchema(
            items=items,
            page=PageMeta(total=total, limit=limit, offset=offset),
        )

    async def get_admin_concept(
        self, *, user: CurrentUser, public_id: str
    ) -> ConceptAdminRead:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concept = await repo.get_admin_concept(public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=public_id)
        items = await self._admin_reads(repo, [concept])
        return items[0]

    async def create_clinic_concept(
        self, *, user: CurrentUser, body: ConceptCreate
    ) -> ConceptAdminRead:
        if body.kind not in CONCEPT_KINDS:
            raise ValidationError(reason="invalid_concept_kind", kind=body.kind)
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        system = await repo.get_internal_code_system()
        if system is None:
            raise ValidationError(reason="code_system_missing")
        existing = await repo.find_concept_by_code(
            code_system_id=system.id, code=body.code
        )
        if existing is not None:
            raise ConflictError(reason="code_taken", code=body.code)
        concept = Concept(
            public_id=new_ulid(),
            code_system_id=system.id,
            code=body.code,
            kind=body.kind,
            sort_order=body.sort_order,
            is_active=True,
            clinic_id=user.clinic_id,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        self._session.add(concept)
        await self._session.flush()
        translation = ConceptTranslation(
            public_id=new_ulid(),
            concept_id=concept.id,
            locale=body.locale,
            display=body.display,
            full_name=body.full_name,
            abbreviation=body.abbreviation,
            patient_friendly=body.patient_friendly,
            clinic_id=user.clinic_id,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        self._session.add(translation)
        await self._session.flush()
        await self._session.refresh(concept)
        self._audit.record_write(
            action="create",
            entity=concept,
            clinic_id=user.clinic_id,
        )
        return (await self._admin_reads(repo, [concept]))[0]

    async def update_clinic_concept(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: ConceptUpdate,
    ) -> ConceptAdminRead:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concept = await self._require_clinic_concept(repo, public_id, user.clinic_id)
        data = body.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(concept, field, value)
        concept.updated_by_id = user.user_id
        self._audit.record_write(
            action="update",
            entity=concept,
            clinic_id=user.clinic_id,
        )
        await self._session.flush()
        return (await self._admin_reads(repo, [concept]))[0]

    async def delete_clinic_concept(self, *, user: CurrentUser, public_id: str) -> None:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concept = await self._require_clinic_concept(repo, public_id, user.clinic_id)
        counts = await repo.reference_counts([concept.id])
        if counts.get(concept.id, 0) > 0:
            raise ConflictError(reason="concept_in_use", publicId=public_id)
        concept.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        concept.deleted_by_id = user.user_id
        concept.is_active = False
        self._audit.record_write(
            action="delete",
            entity=concept,
            clinic_id=user.clinic_id,
        )
        await self._session.flush()

    async def upsert_clinic_translation(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        locale: str,
        body: ConceptTranslationUpsert,
    ) -> ConceptAdminRead:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concept = await repo.get_admin_concept(public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=public_id)
        existing = await repo.find_clinic_translation(
            concept_id=concept.id, locale=locale
        )
        if existing is None:
            existing = ConceptTranslation(
                public_id=new_ulid(),
                concept_id=concept.id,
                locale=locale,
                display=body.display,
                full_name=body.full_name,
                abbreviation=body.abbreviation,
                patient_friendly=body.patient_friendly,
                synonyms=body.synonyms,
                clinic_id=user.clinic_id,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            self._session.add(existing)
        else:
            existing.display = body.display
            existing.full_name = body.full_name
            existing.abbreviation = body.abbreviation
            existing.patient_friendly = body.patient_friendly
            existing.synonyms = body.synonyms
            existing.updated_by_id = user.user_id
        await self._session.flush()
        await self._session.refresh(existing)
        self._audit.record_write(
            action="update",
            entity=existing,
            clinic_id=user.clinic_id,
        )
        return (await self._admin_reads(repo, [concept]))[0]

    async def list_value_sets(self, *, user: CurrentUser) -> list[ValueSetSummaryRead]:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        rows = await repo.list_value_sets()
        return [
            ValueSetSummaryRead(
                code=row.code,
                name_key=row.name_key,
                description_key=row.description_key,
            )
            for row in rows
        ]

    async def add_clinic_value_set_member(
        self,
        *,
        user: CurrentUser,
        code: str,
        body: ValueSetMemberCreate,
    ) -> ValueSetRead:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        value_set = await repo.get_value_set_by_code(code)
        if value_set is None:
            raise NotFoundError(resource="value_set", code=code)
        concept = await repo.get_admin_concept(body.concept_public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=body.concept_public_id)
        existing = await repo.find_clinic_member(
            value_set_id=value_set.id, concept_id=concept.id
        )
        if existing is not None:
            raise ConflictError(
                reason="member_exists", conceptPublicId=concept.public_id
            )
        member = ValueSetMember(
            public_id=new_ulid(),
            value_set_id=value_set.id,
            concept_id=concept.id,
            sort_order=body.sort_order,
            is_default=body.is_default,
            clinic_id=user.clinic_id,
        )
        self._session.add(member)
        await self._session.flush()
        return await self.get_value_set(user=user, code=code, locale=None)

    async def update_clinic_value_set_member(
        self,
        *,
        user: CurrentUser,
        code: str,
        concept_public_id: str,
        body: ValueSetMemberUpdate,
    ) -> ValueSetRead:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        value_set = await repo.get_value_set_by_code(code)
        if value_set is None:
            raise NotFoundError(resource="value_set", code=code)
        concept = await repo.get_admin_concept(concept_public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=concept_public_id)
        member = await repo.find_clinic_member(
            value_set_id=value_set.id, concept_id=concept.id
        )
        if member is None:
            raise NotFoundError(
                resource="value_set_member", public_id=concept_public_id
            )
        data = body.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(member, field, value)
        await self._session.flush()
        return await self.get_value_set(user=user, code=code, locale=None)

    async def remove_clinic_value_set_member(
        self,
        *,
        user: CurrentUser,
        code: str,
        concept_public_id: str,
    ) -> ValueSetRead:
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        value_set = await repo.get_value_set_by_code(code)
        if value_set is None:
            raise NotFoundError(resource="value_set", code=code)
        concept = await repo.get_admin_concept(concept_public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=concept_public_id)
        member = await repo.find_clinic_member(
            value_set_id=value_set.id, concept_id=concept.id
        )
        if member is None:
            raise NotFoundError(
                resource="value_set_member", public_id=concept_public_id
            )
        member.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return await self.get_value_set(user=user, code=code, locale=None)

    async def translation_coverage(
        self,
        *,
        user: CurrentUser,
        locale: str,
        limit: int,
        offset: int,
    ) -> PageSchema[TranslationCoverageItem]:
        clinic = await self._clinic(user.clinic_id)
        repo = TerminologyRepository(self._session, clinic_id=user.clinic_id)
        concepts = await repo.list_concepts_by_kinds(None)
        translations = await repo.load_translations_for_concepts(
            [c.id for c in concepts]
        )
        counts = await repo.reference_counts([c.id for c in concepts])
        gaps: list[TranslationCoverageItem] = []
        for concept in concepts:
            rows = translations.get(concept.id, [])
            has_locale = any(row.locale == locale for row in rows)
            if has_locale:
                continue
            display = repo.resolve_display(
                concept=concept,
                translations=rows,
                locale=locale,
                clinic_default_locale=clinic.default_locale,
            )
            gaps.append(
                TranslationCoverageItem(
                    public_id=concept.public_id,
                    code=concept.code,
                    kind=concept.kind,
                    usage_count=counts.get(concept.id, 0),
                    display=display.display,
                )
            )
        gaps.sort(key=lambda item: (-item.usage_count, item.kind, item.code))
        page_items = gaps[offset : offset + limit]
        return PageSchema(
            items=page_items,
            page=PageMeta(total=len(gaps), limit=limit, offset=offset),
        )

    async def _require_clinic_concept(
        self,
        repo: TerminologyRepository,
        public_id: str,
        clinic_id: int,
    ) -> Concept:
        concept = await repo.get_admin_concept(public_id)
        if concept is None or concept.clinic_id != clinic_id:
            raise NotFoundError(resource="concept", public_id=public_id)
        return concept

    async def _admin_reads(
        self,
        repo: TerminologyRepository,
        concepts: list[Concept],
    ) -> list[ConceptAdminRead]:
        translations = await repo.load_translations_for_concepts(
            [c.id for c in concepts]
        )
        items: list[ConceptAdminRead] = []
        for concept in concepts:
            rows = translations.get(concept.id, [])
            items.append(
                ConceptAdminRead(
                    public_id=concept.public_id,
                    code=concept.code,
                    kind=concept.kind,
                    is_active=concept.is_active,
                    clinic_owned=concept.clinic_id is not None,
                    sort_order=concept.sort_order,
                    translations=[
                        ConceptTranslationRead(
                            locale=row.locale,
                            display=row.display,
                            full_name=row.full_name,
                            abbreviation=row.abbreviation,
                            patient_friendly=row.patient_friendly,
                            synonyms=(
                                row.synonyms if isinstance(row.synonyms, list) else None
                            ),
                            clinic_owned=row.clinic_id is not None,
                        )
                        for row in rows
                    ],
                )
            )
        return items

    async def _clinic(self, clinic_id: int) -> Clinic:
        result = await self._session.execute(
            select(Clinic).where(Clinic.id == clinic_id)
        )
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
        translations = await repo.load_translations_for_concepts(
            [c.id for c in concepts]
        )
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
