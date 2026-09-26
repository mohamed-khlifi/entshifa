"""Seed internal ENT terminology (anatomy + a small findings value set)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.features.terminology.models import (
    CodeSystem,
    Concept,
    ConceptRelationship,
    ConceptTranslation,
    ValueSet,
    ValueSetMember,
)

INTERNAL_SYSTEM_CODE = "INTERNAL"
TM_FINDINGS_VALUE_SET = "tm.findings"


@dataclass(frozen=True, slots=True)
class _Translation:
    locale: str
    display: str
    full_name: str | None = None
    synonyms: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _ConceptSeed:
    code: str
    kind: str
    translations: tuple[_Translation, ...]
    parent_code: str | None = None
    relationship: str | None = None


ANATOMY: tuple[_ConceptSeed, ...] = (
    _ConceptSeed(
        code="ANAT.EAR",
        kind="anatomy",
        translations=(
            _Translation("en", "Ear", "Ear"),
            _Translation("fr", "Oreille", "Oreille"),
        ),
    ),
    _ConceptSeed(
        code="ANAT.EAR.EXTERNAL",
        kind="anatomy",
        parent_code="ANAT.EAR",
        relationship="part_of",
        translations=(
            _Translation("en", "External ear", "External ear"),
            _Translation("fr", "Oreille externe", "Oreille externe"),
        ),
    ),
    _ConceptSeed(
        code="ANAT.EAR.MIDDLE",
        kind="anatomy",
        parent_code="ANAT.EAR",
        relationship="part_of",
        translations=(
            _Translation("en", "Middle ear", "Middle ear"),
            _Translation("fr", "Oreille moyenne", "Oreille moyenne"),
        ),
    ),
    _ConceptSeed(
        code="ANAT.EAR.INNER",
        kind="anatomy",
        parent_code="ANAT.EAR",
        relationship="part_of",
        translations=(
            _Translation("en", "Inner ear", "Inner ear"),
            _Translation("fr", "Oreille interne", "Oreille interne"),
        ),
    ),
    _ConceptSeed(
        code="ANAT.TM",
        kind="anatomy",
        parent_code="ANAT.EAR.MIDDLE",
        relationship="part_of",
        translations=(
            _Translation("en", "Tympanic membrane", "Tympanic membrane", ("eardrum",)),
            _Translation(
                "fr", "Membrane tympanique", "Membrane tympanique", ("tympan",)
            ),
        ),
    ),
    _ConceptSeed(
        code="ANAT.NOSE",
        kind="anatomy",
        translations=(
            _Translation("en", "Nose", "Nose"),
            _Translation("fr", "Nez", "Nez"),
        ),
    ),
    _ConceptSeed(
        code="ANAT.NASAL_CAVITY",
        kind="anatomy",
        parent_code="ANAT.NOSE",
        relationship="part_of",
        translations=(
            _Translation("en", "Nasal cavity", "Nasal cavity"),
            _Translation("fr", "Fosse nasale", "Fosse nasale", ("cavité nasale",)),
        ),
    ),
    _ConceptSeed(
        code="ANAT.LARYNX",
        kind="anatomy",
        translations=(
            _Translation("en", "Larynx", "Larynx"),
            _Translation("fr", "Larynx", "Larynx"),
        ),
    ),
)

FINDINGS: tuple[_ConceptSeed, ...] = (
    _ConceptSeed(
        code="FIND.TM.NORMAL",
        kind="finding",
        translations=(
            _Translation("en", "Normal", "Normal tympanic membrane"),
            _Translation("fr", "Normal", "Membrane tympanique normale"),
        ),
    ),
    _ConceptSeed(
        code="FIND.TM.PERFORATION",
        kind="finding",
        translations=(
            _Translation(
                "en",
                "Perforation",
                "Tympanic membrane perforation",
                ("hole",),
            ),
            _Translation(
                "fr",
                "Perforation",
                "Perforation de la membrane tympanique",
                ("pérforation", "trou"),
            ),
        ),
    ),
    _ConceptSeed(
        code="FIND.TM.RETRACTION",
        kind="finding",
        translations=(
            _Translation("en", "Retraction", "Tympanic membrane retraction"),
            _Translation("fr", "Rétraction", "Rétraction de la membrane tympanique"),
        ),
    ),
    _ConceptSeed(
        code="FIND.TM.EFFUSION",
        kind="finding",
        translations=(
            _Translation("en", "Effusion", "Middle ear effusion"),
            _Translation("fr", "Épanchement", "Épanchement de l'oreille moyenne"),
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class TerminologySeedReport:
    code_systems: int
    concepts: int
    translations: int
    value_sets: int
    members: int


async def seed_terminology(session: AsyncSession) -> TerminologySeedReport:
    system = await _ensure_code_system(session)
    concepts_created = 0
    translations_created = 0
    by_code: dict[str, Concept] = {}

    for index, seed in enumerate((*ANATOMY, *FINDINGS)):
        parent = by_code.get(seed.parent_code) if seed.parent_code else None
        concept, created = await _ensure_concept(
            session,
            system=system,
            seed=seed,
            sort_order=index,
            parent_id=parent.id if parent else None,
        )
        by_code[seed.code] = concept
        if created:
            concepts_created += 1
        translations_created += await _ensure_translations(
            session, concept, seed.translations
        )

    relationships = 0
    for seed in (*ANATOMY, *FINDINGS):
        if seed.parent_code and seed.relationship:
            parent = by_code[seed.parent_code]
            child = by_code[seed.code]
            relationships += await _ensure_relationship(
                session,
                source=child,
                target=parent,
                rel_type=seed.relationship,
            )

    value_set, vs_created = await _ensure_value_set(session)
    members_created = 0
    for index, seed in enumerate(FINDINGS):
        members_created += await _ensure_member(
            session,
            value_set=value_set,
            concept=by_code[seed.code],
            sort_order=index,
            is_default=seed.code == "FIND.TM.NORMAL",
        )

    return TerminologySeedReport(
        code_systems=1 if system else 0,
        concepts=concepts_created,
        translations=translations_created,
        value_sets=1 if vs_created else 0,
        members=members_created,
    )


async def _ensure_code_system(session: AsyncSession) -> CodeSystem:
    existing = (
        await session.execute(
            select(CodeSystem).where(
                CodeSystem.code == INTERNAL_SYSTEM_CODE,
                CodeSystem.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    row = CodeSystem(
        public_id=new_ulid(),
        code=INTERNAL_SYSTEM_CODE,
        name="EntShifa internal terminology",
        version="0.1.0",
        uri="https://entshifa.local/terminology/internal",
    )
    session.add(row)
    await session.flush()
    return row


async def _ensure_concept(
    session: AsyncSession,
    *,
    system: CodeSystem,
    seed: _ConceptSeed,
    sort_order: int,
    parent_id: int | None,
) -> tuple[Concept, bool]:
    existing = (
        await session.execute(
            select(Concept).where(
                Concept.code_system_id == system.id,
                Concept.code == seed.code,
                Concept.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False
    row = Concept(
        public_id=new_ulid(),
        code_system_id=system.id,
        code=seed.code,
        kind=seed.kind,
        parent_id=parent_id,
        sort_order=sort_order,
        is_active=True,
        clinic_id=None,
    )
    session.add(row)
    await session.flush()
    return row, True


async def _ensure_translations(
    session: AsyncSession,
    concept: Concept,
    translations: tuple[_Translation, ...],
) -> int:
    created = 0
    for item in translations:
        existing = (
            await session.execute(
                select(ConceptTranslation).where(
                    ConceptTranslation.concept_id == concept.id,
                    ConceptTranslation.locale == item.locale,
                    ConceptTranslation.clinic_id.is_(None),
                    ConceptTranslation.deleted_at.is_(None),
                ),
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(
            ConceptTranslation(
                public_id=new_ulid(),
                concept_id=concept.id,
                locale=item.locale,
                display=item.display,
                full_name=item.full_name,
                synonyms=list(item.synonyms) if item.synonyms else None,
                clinic_id=None,
            ),
        )
        created += 1
    await session.flush()
    return created


async def _ensure_relationship(
    session: AsyncSession,
    *,
    source: Concept,
    target: Concept,
    rel_type: str,
) -> int:
    existing = (
        await session.execute(
            select(ConceptRelationship).where(
                ConceptRelationship.source_concept_id == source.id,
                ConceptRelationship.target_concept_id == target.id,
                ConceptRelationship.type == rel_type,
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return 0
    session.add(
        ConceptRelationship(
            public_id=new_ulid(),
            source_concept_id=source.id,
            target_concept_id=target.id,
            type=rel_type,
        ),
    )
    await session.flush()
    return 1


async def _ensure_value_set(session: AsyncSession) -> tuple[ValueSet, bool]:
    existing = (
        await session.execute(
            select(ValueSet).where(
                ValueSet.code == TM_FINDINGS_VALUE_SET,
                ValueSet.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False
    row = ValueSet(
        public_id=new_ulid(),
        code=TM_FINDINGS_VALUE_SET,
        name_key="terminology.valueSet.tmFindings",
        description_key="terminology.valueSet.tmFindings.description",
    )
    session.add(row)
    await session.flush()
    return row, True


async def _ensure_member(
    session: AsyncSession,
    *,
    value_set: ValueSet,
    concept: Concept,
    sort_order: int,
    is_default: bool,
) -> int:
    existing = (
        await session.execute(
            select(ValueSetMember).where(
                ValueSetMember.value_set_id == value_set.id,
                ValueSetMember.concept_id == concept.id,
                ValueSetMember.clinic_id.is_(None),
                ValueSetMember.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return 0
    session.add(
        ValueSetMember(
            public_id=new_ulid(),
            value_set_id=value_set.id,
            concept_id=concept.id,
            sort_order=sort_order,
            is_default=is_default,
            clinic_id=None,
        ),
    )
    await session.flush()
    return 1
