"""Anatomy, findings, and value sets for the four examination maps (P2-04).

Narrative phrase templates live on ``concept.properties["narrative"]``.
Arabic finding phrases are short structured glosses.
# VERIFY: Arabic narrative phrases with a clinician before they are used in signed reports.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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


def _anatomy(code: str, parent: str | None, en: str, fr: str, ar: str) -> _ConceptSeed:
    return _ConceptSeed(
        code=code,
        kind="anatomy",
        parent_code=parent,
        relationship="part_of" if parent else None,
        translations=_labels(en, fr, ar),
    )


def _finding(
    code: str,
    en: str,
    fr: str,
    ar: str,
    *,
    en_phrase: str,
    fr_phrase: str,
    ar_phrase: str,
) -> _ConceptSeed:
    return _ConceptSeed(
        code=code,
        kind="finding",
        narrative={"en": en_phrase, "fr": fr_phrase, "ar": ar_phrase},
        translations=_labels(en, fr, ar),
    )


def _site(word_en: str, word_fr: str, word_ar: str) -> dict[str, str]:
    return {
        "en_phrase": f"{{{{bodySite}}}}: {word_en}",
        "fr_phrase": f"{{{{bodySite}}}} : {word_fr}",
        "ar_phrase": f"{{{{bodySite}}}}: {word_ar}",
    }


MAP_CONCEPTS: tuple[_ConceptSeed, ...] = (
    _anatomy(
        "ANAT.EAR.CANAL",
        "ANAT.EAR.EXTERNAL",
        "External auditory canal",
        "Conduit auditif externe",
        "الصماخ السمعي الظاهر",
    ),
    _anatomy(
        "ANAT.TM.PF",
        "ANAT.TM",
        "Pars flaccida",
        "Pars flaccida",
        "الجزء الرخو",
    ),
    _anatomy(
        "ANAT.TM.PT.AS",
        "ANAT.TM",
        "Anterosuperior quadrant",
        "Quadrant antéro-supérieur",
        "الربع الأمامي العلوي",
    ),
    _anatomy(
        "ANAT.TM.PT.AI",
        "ANAT.TM",
        "Anteroinferior quadrant",
        "Quadrant antéro-inférieur",
        "الربع الأمامي السفلي",
    ),
    _anatomy(
        "ANAT.TM.PT.PS",
        "ANAT.TM",
        "Posterosuperior quadrant",
        "Quadrant postéro-supérieur",
        "الربع الخلفي العلوي",
    ),
    _anatomy(
        "ANAT.TM.PT.PI",
        "ANAT.TM",
        "Posteroinferior quadrant",
        "Quadrant postéro-inférieur",
        "الربع الخلفي السفلي",
    ),
    _anatomy(
        "ANAT.NASAL.VESTIBULE",
        "ANAT.NASAL_CAVITY",
        "Nasal vestibule",
        "Vestibule nasal",
        "دهليز الأنف",
    ),
    _anatomy(
        "ANAT.NASAL.VALVE",
        "ANAT.NASAL_CAVITY",
        "Nasal valve",
        "Valve nasale",
        "الصمام الأنفي",
    ),
    _anatomy(
        "ANAT.NASAL.SEPTUM",
        "ANAT.NASAL_CAVITY",
        "Nasal septum",
        "Septum nasal",
        "الحاجز الأنفي",
    ),
    _anatomy(
        "ANAT.NASAL.INFERIOR_TURBINATE",
        "ANAT.NASAL_CAVITY",
        "Inferior turbinate",
        "Cornet inférieur",
        "القرين السفلي",
    ),
    _anatomy(
        "ANAT.NASAL.MIDDLE_TURBINATE",
        "ANAT.NASAL_CAVITY",
        "Middle turbinate",
        "Cornet moyen",
        "القرين الأوسط",
    ),
    _anatomy(
        "ANAT.NASAL.MUCOSA",
        "ANAT.NASAL_CAVITY",
        "Nasal mucosa",
        "Muqueuse nasale",
        "المخاطية الأنفية",
    ),
    _anatomy("ANAT.ORAL", None, "Oral cavity", "Cavité orale", "جوف الفم"),
    _anatomy("ANAT.ORAL.LIPS", "ANAT.ORAL", "Lips", "Lèvres", "الشفتان"),
    _anatomy("ANAT.ORAL.TONGUE", "ANAT.ORAL", "Tongue", "Langue", "اللسان"),
    _anatomy(
        "ANAT.ORAL.SOFT_PALATE",
        "ANAT.ORAL",
        "Soft palate",
        "Palais mou",
        "الحنك الرخو",
    ),
    _anatomy("ANAT.ORAL.TONSIL", "ANAT.ORAL", "Tonsil", "Amygdale", "اللوزة"),
    _anatomy(
        "ANAT.ORAL.POSTERIOR_WALL",
        "ANAT.ORAL",
        "Posterior pharyngeal wall",
        "Paroi pharyngée postérieure",
        "الجدار الخلفي للبلعوم",
    ),
    _anatomy("ANAT.NECK", None, "Neck", "Cou", "العنق"),
    _anatomy(
        "ANAT.PAROTID", "ANAT.NECK", "Parotid gland", "Glande parotide", "النكفية"
    ),
    _anatomy("ANAT.NECK.IA", "ANAT.NECK", "Level IA", "Niveau IA", "المستوى IA"),
    _anatomy("ANAT.NECK.IB", "ANAT.NECK", "Level IB", "Niveau IB", "المستوى IB"),
    _anatomy("ANAT.NECK.IIA", "ANAT.NECK", "Level IIA", "Niveau IIA", "المستوى IIA"),
    _anatomy("ANAT.NECK.IIB", "ANAT.NECK", "Level IIB", "Niveau IIB", "المستوى IIB"),
    _anatomy(
        "ANAT.SUBMANDIBULAR",
        "ANAT.NECK",
        "Submandibular gland",
        "Glande sous-mandibulaire",
        "الغدة تحت الفك",
    ),
    _anatomy("ANAT.NECK.III", "ANAT.NECK", "Level III", "Niveau III", "المستوى III"),
    _anatomy("ANAT.NECK.IV", "ANAT.NECK", "Level IV", "Niveau IV", "المستوى IV"),
    _anatomy("ANAT.NECK.VA", "ANAT.NECK", "Level VA", "Niveau VA", "المستوى VA"),
    _anatomy("ANAT.NECK.VB", "ANAT.NECK", "Level VB", "Niveau VB", "المستوى VB"),
    _anatomy("ANAT.NECK.VI", "ANAT.NECK", "Level VI", "Niveau VI", "المستوى VI"),
    _anatomy("ANAT.THYROID", "ANAT.NECK", "Thyroid", "Thyroïde", "الدرقية"),
    _anatomy(
        "ANAT.THYROID.LOBE",
        "ANAT.THYROID",
        "Thyroid lobe",
        "Lobe thyroïdien",
        "فص الدرقية",
    ),
    _anatomy(
        "ANAT.THYROID.ISTHMUS",
        "ANAT.THYROID",
        "Thyroid isthmus",
        "Isthme thyroïdien",
        "برزخ الدرقية",
    ),
    _anatomy("ANAT.NECK.VII", "ANAT.NECK", "Level VII", "Niveau VII", "المستوى VII"),
    _finding(
        "FIND.CANAL.NORMAL",
        "Normal",
        "Normal",
        "طبيعي",
        **_site("normal", "normal", "طبيعي"),
    ),
    _finding(
        "FIND.CANAL.WAX",
        "Wax",
        "Cérumen",
        "صملاخ",
        **_site("wax", "cérumen", "صملاخ"),
    ),
    _finding(
        "FIND.CANAL.OTITIS_EXTERNA",
        "Otitis externa",
        "Otite externe",
        "التهاب الأذن الظاهرة",
        **_site("otitis externa", "otite externe", "التهاب الأذن الظاهرة"),
    ),
    _finding(
        "FIND.NOSE.NORMAL",
        "Normal",
        "Normal",
        "طبيعي",
        **_site("normal", "normal", "طبيعي"),
    ),
    _finding(
        "FIND.NOSE.SEPTAL_DEVIATION",
        "Septal deviation",
        "Déviation septale",
        "انحراف الحاجز",
        **_site("septal deviation", "déviation septale", "انحراف الحاجز"),
    ),
    _finding(
        "FIND.NOSE.TURBINATE_HYPERTROPHY",
        "Turbinate hypertrophy",
        "Hypertrophie du cornet",
        "تضخم القرين",
        **_site("turbinate hypertrophy", "hypertrophie du cornet", "تضخم القرين"),
    ),
    _finding(
        "FIND.NOSE.MUCOSA_CONGESTED",
        "Congested mucosa",
        "Muqueuse congestive",
        "مخاطية محتقنة",
        **_site("congested mucosa", "muqueuse congestive", "مخاطية محتقنة"),
    ),
    _finding(
        "FIND.NOSE.POLYP",
        "Polyp",
        "Polype",
        "سليلة",
        **_site("polyp", "polype", "سليلة"),
    ),
    _finding(
        "FIND.NOSE.DISCHARGE",
        "Discharge",
        "Sécrétions",
        "مفرزات",
        **_site("discharge", "sécrétions", "مفرزات"),
    ),
    _finding(
        "FIND.ORAL.NORMAL",
        "Normal",
        "Normal",
        "طبيعي",
        **_site("normal", "normal", "طبيعي"),
    ),
    _finding(
        "FIND.ORAL.ULCER",
        "Ulcer",
        "Ulcération",
        "قرحة",
        **_site("ulcer", "ulcération", "قرحة"),
    ),
    _finding(
        "FIND.ORAL.LEUKOPLAKIA",
        "Leukoplakia",
        "Leucoplasie",
        "طلاوة",
        **_site("leukoplakia", "leucoplasie", "طلاوة"),
    ),
    _finding(
        "FIND.ORAL.ERYTHEMA",
        "Erythema",
        "Érythème",
        "حمامى",
        **_site("erythema", "érythème", "حمامى"),
    ),
    _finding(
        "FIND.TONSIL.NORMAL",
        "Brodsky grade 0",
        "Grade de Brodsky 0",
        "درجة برودسكي 0",
        **_site("Brodsky grade 0", "grade de Brodsky 0", "درجة برودسكي 0"),
    ),
    _finding(
        "FIND.TONSIL.BRODSKY_1",
        "Brodsky grade 1",
        "Grade de Brodsky 1",
        "درجة برودسكي 1",
        **_site("Brodsky grade 1", "grade de Brodsky 1", "درجة برودسكي 1"),
    ),
    _finding(
        "FIND.TONSIL.BRODSKY_2",
        "Brodsky grade 2",
        "Grade de Brodsky 2",
        "درجة برودسكي 2",
        **_site("Brodsky grade 2", "grade de Brodsky 2", "درجة برودسكي 2"),
    ),
    _finding(
        "FIND.TONSIL.BRODSKY_3",
        "Brodsky grade 3",
        "Grade de Brodsky 3",
        "درجة برودسكي 3",
        **_site("Brodsky grade 3", "grade de Brodsky 3", "درجة برودسكي 3"),
    ),
    _finding(
        "FIND.TONSIL.BRODSKY_4",
        "Brodsky grade 4",
        "Grade de Brodsky 4",
        "درجة برودسكي 4",
        **_site("Brodsky grade 4", "grade de Brodsky 4", "درجة برودسكي 4"),
    ),
    _finding(
        "FIND.TONSIL.EXUDATE",
        "Exudate",
        "Exsudat",
        "نتح",
        **_site("exudate", "exsudat", "نتح"),
    ),
    _finding(
        "FIND.NECK.NORMAL",
        "Normal",
        "Normal",
        "طبيعي",
        **_site("normal", "normal", "طبيعي"),
    ),
    _finding(
        "FIND.NECK.LYMPHADENOPATHY",
        "Lymphadenopathy",
        "Adénopathie",
        "ضخامة عقدية",
        **_site("lymphadenopathy", "adénopathie", "ضخامة عقدية"),
    ),
    _finding(
        "FIND.THYROID.NORMAL",
        "Normal",
        "Normale",
        "طبيعية",
        **_site("normal", "normale", "طبيعية"),
    ),
    _finding(
        "FIND.THYROID.ENLARGED",
        "Enlarged",
        "Augmentée de volume",
        "متضخمة",
        **_site("enlarged", "augmentée de volume", "متضخمة"),
    ),
    _finding(
        "FIND.THYROID.NODULE",
        "Nodule",
        "Nodule",
        "عقيدة",
        **_site("nodule", "nodule", "عقيدة"),
    ),
    _finding(
        "FIND.SALIVARY.NORMAL",
        "Normal",
        "Normale",
        "طبيعية",
        **_site("normal", "normale", "طبيعية"),
    ),
    _finding(
        "FIND.SALIVARY.SWELLING",
        "Swelling",
        "Tuméfaction",
        "تورم",
        **_site("swelling", "tuméfaction", "تورم"),
    ),
)

# (value set code, name key, members as (concept code, is_default))
MAP_VALUE_SETS: tuple[tuple[str, str, tuple[tuple[str, bool], ...]], ...] = (
    (
        "tm.canal.findings",
        "terminology.valueSet.tmCanalFindings",
        (
            ("FIND.CANAL.NORMAL", True),
            ("FIND.CANAL.WAX", False),
            ("FIND.CANAL.OTITIS_EXTERNA", False),
        ),
    ),
    (
        "nose.findings",
        "terminology.valueSet.noseFindings",
        (
            ("FIND.NOSE.NORMAL", True),
            ("FIND.NOSE.SEPTAL_DEVIATION", False),
            ("FIND.NOSE.TURBINATE_HYPERTROPHY", False),
            ("FIND.NOSE.MUCOSA_CONGESTED", False),
            ("FIND.NOSE.POLYP", False),
            ("FIND.NOSE.DISCHARGE", False),
        ),
    ),
    (
        "oral.findings",
        "terminology.valueSet.oralFindings",
        (
            ("FIND.ORAL.NORMAL", True),
            ("FIND.ORAL.ULCER", False),
            ("FIND.ORAL.LEUKOPLAKIA", False),
            ("FIND.ORAL.ERYTHEMA", False),
        ),
    ),
    (
        "oral.tonsil.findings",
        "terminology.valueSet.tonsilFindings",
        (
            ("FIND.TONSIL.NORMAL", True),
            ("FIND.TONSIL.BRODSKY_1", False),
            ("FIND.TONSIL.BRODSKY_2", False),
            ("FIND.TONSIL.BRODSKY_3", False),
            ("FIND.TONSIL.BRODSKY_4", False),
            ("FIND.TONSIL.EXUDATE", False),
        ),
    ),
    (
        "neck.level.findings",
        "terminology.valueSet.neckLevelFindings",
        (
            ("FIND.NECK.NORMAL", True),
            ("FIND.NECK.LYMPHADENOPATHY", False),
        ),
    ),
    (
        "neck.thyroid.findings",
        "terminology.valueSet.thyroidFindings",
        (
            ("FIND.THYROID.NORMAL", True),
            ("FIND.THYROID.ENLARGED", False),
            ("FIND.THYROID.NODULE", False),
        ),
    ),
    (
        "neck.salivary.findings",
        "terminology.valueSet.salivaryFindings",
        (
            ("FIND.SALIVARY.NORMAL", True),
            ("FIND.SALIVARY.SWELLING", False),
        ),
    ),
)


async def seed_anatomy_maps(
    session: AsyncSession,
    system: CodeSystem,
    by_code: dict[str, Concept],
) -> TerminologySeedReport:
    concepts_created = 0
    translations_created = 0
    for index, seed in enumerate(MAP_CONCEPTS):
        parent = by_code.get(seed.parent_code) if seed.parent_code else None
        concept, created = await _ensure_concept(
            session,
            system=system,
            seed=seed,
            sort_order=1000 + index,
            parent_id=parent.id if parent else None,
        )
        by_code[seed.code] = concept
        if created:
            concepts_created += 1
        translations_created += await _ensure_translations(
            session, concept, seed.translations
        )

    for seed in MAP_CONCEPTS:
        if seed.parent_code and seed.relationship:
            await _ensure_relationship(
                session,
                source=by_code[seed.code],
                target=by_code[seed.parent_code],
                rel_type=seed.relationship,
            )

    value_sets = 0
    members = 0
    for code, name_key, rows in MAP_VALUE_SETS:
        value_set, created = await _ensure_coded_value_set(
            session,
            code=code,
            name_key=name_key,
            description_key=f"{name_key}.description",
        )
        if created:
            value_sets += 1
        for index, (concept_code, is_default) in enumerate(rows):
            members += await _ensure_member(
                session,
                value_set=value_set,
                concept=by_code[concept_code],
                sort_order=index,
                is_default=is_default,
            )

    return TerminologySeedReport(
        code_systems=0,
        concepts=concepts_created,
        translations=translations_created,
        value_sets=value_sets,
        members=members,
    )
