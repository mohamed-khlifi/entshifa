"""Global drug catalog. Dosing rules are clinic formulary rows, not this seed.

Identities follow feature spec section 12.2 plus gentamicin, which the spec
lists as an ototoxic aminoglycoside. No mg/kg numbers are stored here.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.features.prescriptions.models import Drug, DrugForm
from ent.features.terminology.models import CodeSystem, Concept, ConceptTranslation
from ent.seeds.terminology import INTERNAL_SYSTEM_CODE


@dataclass(frozen=True, slots=True)
class _DrugSeed:
    code: str
    inn_name: str
    atc_code: str
    drug_class: str
    is_ototoxic: bool
    forms: tuple[str, ...]
    en: str
    fr: str
    ar: str


# ATC codes are the WHO ATC/DDD index identities, not doses.
DRUGS: tuple[_DrugSeed, ...] = (
    _DrugSeed(
        "DRUG.AMOXICILLIN",
        "amoxicillin",
        "J01CA04",
        "penicillin",
        False,
        ("tablet", "syrup"),
        "Amoxicillin",
        "Amoxicilline",
        "أموكسيسيلين",
    ),
    _DrugSeed(
        "DRUG.AMOXICILLIN_CLAVULANATE",
        "amoxicillin-clavulanate",
        "J01CR02",
        "penicillin",
        False,
        ("tablet", "syrup"),
        "Amoxicillin and clavulanate",
        "Amoxicilline et acide clavulanique",
        "أموكسيسيلين وكلافولانات",
    ),
    _DrugSeed(
        "DRUG.CEFUROXIME",
        "cefuroxime",
        "J01DC02",
        "cephalosporin",
        False,
        ("tablet",),
        "Cefuroxime",
        "Céfuroxime",
        "سيفوروكسيم",
    ),
    _DrugSeed(
        "DRUG.CEFPODOXIME",
        "cefpodoxime",
        "J01DD13",
        "cephalosporin",
        False,
        ("tablet",),
        "Cefpodoxime",
        "Cefpodoxime",
        "سيفبودوكسيم",
    ),
    _DrugSeed(
        "DRUG.AZITHROMYCIN",
        "azithromycin",
        "J01FA10",
        "macrolide",
        False,
        ("tablet", "syrup"),
        "Azithromycin",
        "Azithromycine",
        "أزيثروميسين",
    ),
    _DrugSeed(
        "DRUG.CLINDAMYCIN",
        "clindamycin",
        "J01FF01",
        "lincosamide",
        False,
        ("tablet",),
        "Clindamycin",
        "Clindamycine",
        "كليندامايسين",
    ),
    _DrugSeed(
        "DRUG.PREDNISOLONE",
        "prednisolone",
        "H02AB06",
        "corticosteroid",
        False,
        ("tablet",),
        "Prednisolone",
        "Prednisolone",
        "بريدنيزولون",
    ),
    _DrugSeed(
        "DRUG.PARACETAMOL",
        "paracetamol",
        "N02BE01",
        "analgesic",
        False,
        ("tablet", "syrup"),
        "Paracetamol",
        "Paracétamol",
        "باراسيتامول",
    ),
    _DrugSeed(
        "DRUG.IBUPROFEN",
        "ibuprofen",
        "M01AE01",
        "nsaid",
        False,
        ("tablet", "syrup"),
        "Ibuprofen",
        "Ibuprofène",
        "إيبوبروفين",
    ),
    _DrugSeed(
        "DRUG.CETIRIZINE",
        "cetirizine",
        "R06AE07",
        "antihistamine",
        False,
        ("tablet", "syrup"),
        "Cetirizine",
        "Cétirizine",
        "سيتيريزين",
    ),
    _DrugSeed(
        "DRUG.DESLORATADINE",
        "desloratadine",
        "R06AX27",
        "antihistamine",
        False,
        ("tablet", "syrup"),
        "Desloratadine",
        "Desloratadine",
        "ديسلوراتادين",
    ),
    _DrugSeed(
        "DRUG.MONTELUKAST",
        "montelukast",
        "R03DC03",
        "leukotriene_antagonist",
        False,
        ("tablet",),
        "Montelukast",
        "Montélukast",
        "مونتيلوكاست",
    ),
    _DrugSeed(
        "DRUG.GENTAMICIN",
        "gentamicin",
        "J01GB03",
        "aminoglycoside",
        True,
        ("injection",),
        "Gentamicin",
        "Gentamicine",
        "جنتاميسين",
    ),
)


@dataclass(frozen=True, slots=True)
class FormularySeedReport:
    drugs_created: int
    forms_created: int


async def seed_formulary(session: AsyncSession) -> FormularySeedReport:
    """Idempotent drug and form catalog. Clinics add dosing rules themselves."""

    system = (
        await session.execute(
            select(CodeSystem).where(
                CodeSystem.code == INTERNAL_SYSTEM_CODE,
                CodeSystem.deleted_at.is_(None),
            )
        )
    ).scalar_one()
    drugs_created = 0
    forms_created = 0
    for index, seed in enumerate(DRUGS):
        concept = await _concept(session, system, seed, index)
        drug, created = await _drug(session, seed, int(concept.id))
        drugs_created += int(created)
        for form in seed.forms:
            forms_created += int(await _form(session, drug, form))
    return FormularySeedReport(drugs_created=drugs_created, forms_created=forms_created)


async def _concept(
    session: AsyncSession, system: CodeSystem, seed: _DrugSeed, sort_order: int
) -> Concept:
    existing = (
        await session.execute(
            select(Concept).where(
                Concept.code_system_id == system.id,
                Concept.code == seed.code,
                Concept.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = Concept(
            public_id=new_ulid(),
            code_system_id=int(system.id),
            code=seed.code,
            kind="drug",
            sort_order=sort_order,
            is_active=True,
            clinic_id=None,
        )
        session.add(existing)
        await session.flush()
    for locale, display in (("en", seed.en), ("fr", seed.fr), ("ar", seed.ar)):
        found = (
            await session.execute(
                select(ConceptTranslation).where(
                    ConceptTranslation.concept_id == existing.id,
                    ConceptTranslation.locale == locale,
                    ConceptTranslation.clinic_id.is_(None),
                    ConceptTranslation.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if found is None:
            session.add(
                ConceptTranslation(
                    public_id=new_ulid(),
                    concept_id=int(existing.id),
                    locale=locale,
                    display=display,
                    full_name=display,
                    clinic_id=None,
                )
            )
    await session.flush()
    return existing


async def _drug(
    session: AsyncSession, seed: _DrugSeed, concept_id: int
) -> tuple[Drug, bool]:
    existing = (
        await session.execute(
            select(Drug).where(Drug.code == seed.code, Drug.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.concept_id is None:
            existing.concept_id = concept_id
        return existing, False
    row = Drug(
        public_id=new_ulid(),
        code=seed.code,
        inn_name=seed.inn_name,
        atc_code=seed.atc_code,
        drug_class=seed.drug_class,
        is_ototoxic=seed.is_ototoxic,
        is_anticoagulant=False,
        concept_id=concept_id,
    )
    session.add(row)
    await session.flush()
    return row, True


async def _form(session: AsyncSession, drug: Drug, form: str) -> bool:
    existing = (
        await session.execute(
            select(DrugForm).where(
                DrugForm.drug_id == drug.id,
                DrugForm.form == form,
                DrugForm.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    session.add(
        DrugForm(
            public_id=new_ulid(),
            drug_id=int(drug.id),
            form=form,
        )
    )
    await session.flush()
    return True
