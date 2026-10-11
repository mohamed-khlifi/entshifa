"""Endoscopic anatomy, Lund-Kennedy items, and the nasal endoscopy procedure.

Structure findings stay observations. Score items are explicit ordinals.
# VERIFY: Arabic labels with a clinician before they appear on a signed report.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.endoscopy.constants import (
    ABNORMAL_FINDINGS,
    ADENOID_CODE,
    ENDOSCOPY_STRUCTURE_CODES,
    FINDING_NORMAL,
    FINDING_NOT_VISUALIZED,
    FINDING_UNKNOWN,
    LK_CONCEPT_CODES,
    POLYP_GRADE_CODE,
    PROCEDURE_CODE,
)
from ent.features.terminology.models import CodeSystem, Concept
from ent.seeds.terminology import (
    TerminologySeedReport,
    _ConceptSeed,
    _ensure_coded_value_set,
    _ensure_concept,
    _ensure_member,
    _ensure_relationship,
    _ensure_translations,
    _Translation,
)


def _labels(en: str, fr: str, ar: str) -> tuple[_Translation, ...]:
    return (
        _Translation("en", en, en),
        _Translation("fr", fr, fr),
        _Translation("ar", ar, ar),
    )


_NEW_ANATOMY: tuple[_ConceptSeed, ...] = (
    _ConceptSeed(
        code="ANAT.NASAL.INFERIOR_MEATUS",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Inferior meatus", "Méat inférieur", "الصماخ السفلي"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.MIDDLE_MEATUS",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Middle meatus", "Méat moyen", "الصماخ الأوسط"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.UNCINATE",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Uncinate process", "Processus unciné", "الناتئ المعقوف"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.BULLA",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Ethmoid bulla", "Bulle ethmoïdale", "الفقاعة الغربالية"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.SUPERIOR_TURBINATE",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Superior turbinate", "Cornet supérieur", "القرين العلوي"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.SUPERIOR_MEATUS",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Superior meatus", "Méat supérieur", "الصماخ العلوي"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.SPHENOETHMOIDAL_RECESS",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels(
            "Sphenoethmoidal recess",
            "Récessus sphéno-ethmoïdal",
            "الردب الوتدي الغربالي",
        ),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.OLFACTORY_CLEFT",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Olfactory cleft", "Fente olfactive", "الشق الشمي"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.NASOPHARYNX",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels("Nasopharynx", "Nasopharynx", "البلعوم الأنفي"),
    ),
    _ConceptSeed(
        code="ANAT.NASAL.POST_FESS",
        kind="anatomy",
        parent_code="ANAT.NASAL_CAVITY",
        relationship="part_of",
        translations=_labels(
            "Post-FESS cavity",
            "Cavité après chirurgie endoscopique",
            "جوف ما بعد جراحة الجيوب",
        ),
    ),
)

_FINDINGS: tuple[_ConceptSeed, ...] = (
    _ConceptSeed(
        code=FINDING_NORMAL,
        kind="finding",
        translations=_labels("Normal", "Normal", "طبيعي"),
    ),
    _ConceptSeed(
        code="FIND.ENDO.POLYP",
        kind="finding",
        translations=_labels("Polyp", "Polype", "سليلة"),
    ),
    _ConceptSeed(
        code="FIND.ENDO.EDEMA",
        kind="finding",
        translations=_labels("Edema", "Œdème", "وذمة"),
    ),
    _ConceptSeed(
        code="FIND.ENDO.DISCHARGE",
        kind="finding",
        translations=_labels("Discharge", "Sécrétions", "مفرزات"),
    ),
    _ConceptSeed(
        code="FIND.ENDO.CRUST",
        kind="finding",
        translations=_labels("Crust", "Croûte", "قشرة"),
    ),
    _ConceptSeed(
        code="FIND.ENDO.SYNECHIA",
        kind="finding",
        translations=_labels("Synechia", "Synéchie", "التصاق"),
    ),
    _ConceptSeed(
        code=FINDING_NOT_VISUALIZED,
        kind="finding",
        translations=_labels("Not visualized", "Non visualisé", "غير مرئي"),
    ),
    _ConceptSeed(
        code=FINDING_UNKNOWN,
        kind="finding",
        translations=_labels("Unknown", "Inconnu", "غير معروف"),
    ),
)

_SCORE_LABELS: dict[str, tuple[str, str, str]] = {
    "polyps": ("Polyps", "Polypes", "سلائل"),
    "edema": ("Edema", "Œdème", "وذمة"),
    "discharge": ("Discharge", "Sécrétions", "مفرزات"),
    "scarring": ("Scarring", "Cicatrices", "تندب"),
    "crusting": ("Crusting", "Croûtes", "تقشّر"),
}


def _score_concepts() -> tuple[_ConceptSeed, ...]:
    rows: list[_ConceptSeed] = []
    for item, code in LK_CONCEPT_CODES.items():
        en, fr, ar = _SCORE_LABELS[item]
        rows.append(
            _ConceptSeed(
                code=code,
                kind="qualifier",
                translations=_labels(en, fr, ar),
                properties={
                    "scorable": True,
                    "lund_kennedy_item": item,
                    "modified_lund_kennedy": item in {"polyps", "edema", "discharge"},
                },
            )
        )
    rows.append(
        _ConceptSeed(
            code=POLYP_GRADE_CODE,
            kind="qualifier",
            translations=_labels("Polyp grade", "Grade polypoïde", "درجة السليلة"),
            properties={"scorable": True, "polyp_grade": True},
        )
    )
    rows.append(
        _ConceptSeed(
            code=ADENOID_CODE,
            kind="qualifier",
            translations=_labels(
                "Adenoid obstruction",
                "Obstruction adénoïdienne",
                "انسداد الناميات",
            ),
            properties={"scorable": True, "adenoid_obstruction_pct": True},
        )
    )
    rows.append(
        _ConceptSeed(
            code=PROCEDURE_CODE,
            kind="procedure",
            translations=_labels(
                "Nasal endoscopy",
                "Endoscopie nasale",
                "تنظير الأنف",
            ),
        )
    )
    return tuple(rows)


async def seed_endoscopy(
    session: AsyncSession,
    system: CodeSystem,
    by_code: dict[str, Concept],
) -> TerminologySeedReport:
    concepts_created = 0
    translations_created = 0
    seeds = (*_NEW_ANATOMY, *_FINDINGS, *_score_concepts())
    for index, seed in enumerate(seeds):
        parent = by_code.get(seed.parent_code) if seed.parent_code else None
        concept, created = await _ensure_concept(
            session,
            system=system,
            seed=seed,
            sort_order=2000 + index,
            parent_id=parent.id if parent else None,
        )
        by_code[seed.code] = concept
        if created:
            concepts_created += 1
        translations_created += await _ensure_translations(
            session, concept, seed.translations
        )

    for seed in _NEW_ANATOMY:
        if seed.parent_code and seed.relationship and seed.parent_code in by_code:
            await _ensure_relationship(
                session,
                source=by_code[seed.code],
                target=by_code[seed.parent_code],
                rel_type=seed.relationship,
            )

    value_sets = 0
    members = 0
    structure_set, created = await _ensure_coded_value_set(
        session,
        code="endoscopy.structures",
        name_key="terminology.valueSet.endoscopyStructures",
        description_key="terminology.valueSet.endoscopyStructures.description",
    )
    if created:
        value_sets += 1
    for index, code in enumerate(ENDOSCOPY_STRUCTURE_CODES):
        members += await _ensure_member(
            session,
            value_set=structure_set,
            concept=by_code[code],
            sort_order=index,
            is_default=False,
        )
    finding_order = (
        FINDING_NORMAL,
        *sorted(ABNORMAL_FINDINGS),
        FINDING_NOT_VISUALIZED,
        FINDING_UNKNOWN,
    )
    finding_set, created = await _ensure_coded_value_set(
        session,
        code="endoscopy.findings",
        name_key="terminology.valueSet.endoscopyFindings",
        description_key="terminology.valueSet.endoscopyFindings.description",
    )
    if created:
        value_sets += 1
    for index, code in enumerate(finding_order):
        members += await _ensure_member(
            session,
            value_set=finding_set,
            concept=by_code[code],
            sort_order=index,
            is_default=code == FINDING_NORMAL,
        )
    return TerminologySeedReport(
        code_systems=0,
        concepts=concepts_created,
        translations=translations_created,
        value_sets=value_sets,
        members=members,
    )
