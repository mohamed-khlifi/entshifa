"""Procedure concepts for the short office forms (feature spec §7.4).

# VERIFY: Arabic labels with a clinician before they appear on a signed report.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.office_procedures.constants import (
    PROC_BIOPSY,
    PROC_BOTULINUM,
    PROC_EPISTAXIS,
    PROC_FNA,
    PROC_FRACTURE,
    PROC_PERITONSILLAR,
    PROC_SIALENDOSCOPY,
)
from ent.features.terminology.models import CodeSystem, Concept
from ent.seeds.terminology import (
    TerminologySeedReport,
    _ConceptSeed,
    _ensure_coded_value_set,
    _ensure_concept,
    _ensure_member,
    _ensure_translations,
    _Translation,
)


def _labels(en: str, fr: str, ar: str) -> tuple[_Translation, ...]:
    return (
        _Translation("en", en, en),
        _Translation("fr", fr, fr),
        _Translation("ar", ar, ar),
    )


def _procedure(code: str, en: str, fr: str, ar: str) -> _ConceptSeed:
    return _ConceptSeed(code=code, kind="procedure", translations=_labels(en, fr, ar))


_PROCEDURES = (
    _procedure(
        PROC_EPISTAXIS,
        "Epistaxis management",
        "Prise en charge d'épistaxis",
        "علاج الرعاف",
    ),
    _procedure(
        PROC_FNA,
        "Fine needle aspiration",
        "Cytoponction à l'aiguille fine",
        "شفط بالإبرة الدقيقة",
    ),
    _procedure(
        PROC_BIOPSY,
        "Oral or pharyngeal biopsy",
        "Biopsie buccale ou pharyngée",
        "خزعة الفم أو البلعوم",
    ),
    _procedure(
        PROC_BOTULINUM,
        "Botulinum toxin injection",
        "Injection de toxine botulique",
        "حقن ذيفان الوشيقية",
    ),
    _procedure(
        PROC_PERITONSILLAR,
        "Peritonsillar abscess drainage",
        "Drainage d'abcès péri-amygdalien",
        "تصريف خراج حول اللوزة",
    ),
    _procedure(
        PROC_FRACTURE,
        "Closed reduction of nasal fracture",
        "Réduction fermée de fracture des os propres du nez",
        "رد مغلق لكسر عظام الأنف",
    ),
    _procedure(
        PROC_SIALENDOSCOPY,
        "Sialendoscopy",
        "Sialendoscopie",
        "تنظير الغدة اللعابية",
    ),
)


async def seed_office_procedures(
    session: AsyncSession,
    system: CodeSystem,
    by_code: dict[str, Concept],
) -> TerminologySeedReport:
    concepts_created = 0
    translations_created = 0
    for index, seed in enumerate(_PROCEDURES):
        concept, created = await _ensure_concept(
            session,
            system=system,
            seed=seed,
            sort_order=4600 + index,
            parent_id=None,
        )
        by_code[seed.code] = concept
        if created:
            concepts_created += 1
        translations_created += await _ensure_translations(
            session, concept, seed.translations
        )
    value_set, created = await _ensure_coded_value_set(
        session,
        code="office_procedures.types",
        name_key="terminology.valueSet.officeProcedures",
        description_key="terminology.valueSet.officeProcedures.description",
    )
    members = 0
    for index, seed in enumerate(_PROCEDURES):
        members += await _ensure_member(
            session,
            value_set=value_set,
            concept=by_code[seed.code],
            sort_order=index,
            is_default=False,
        )
    return TerminologySeedReport(
        code_systems=0,
        concepts=concepts_created,
        translations=translations_created,
        value_sets=1 if created else 0,
        members=members,
    )
