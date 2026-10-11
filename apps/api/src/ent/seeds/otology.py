"""Otology procedures, drugs, and the extra tympanic-membrane findings.

# VERIFY: Arabic labels with a clinician before they appear on a signed report.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.otology.constants import (
    CANAL_ABNORMAL,
    CANAL_NORMAL,
    CANAL_NOT_VISUALIZED,
    CANAL_UNKNOWN,
    IT_DRUGS,
    PROC_CAVITY,
    PROC_FOREIGN_BODY,
    PROC_INJECTION,
    PROC_MICROSCOPY,
    PROC_OTOSCOPY,
    PROC_TUBE,
    PROC_TUBE_REMOVAL,
    PROC_WAX,
    PROC_WICK,
    TM_ABNORMAL,
    TM_NORMAL,
    TM_NOT_VISUALIZED,
    TM_UNKNOWN,
)
from ent.features.terminology.models import CodeSystem, Concept
from ent.seeds.terminology import (
    TerminologySeedReport,
    _ConceptSeed,
    _ensure_coded_value_set,
    _ensure_concept,
    _ensure_member,
    _ensure_translations,
    _ensure_value_set,
    _Translation,
)


def _labels(en: str, fr: str, ar: str) -> tuple[_Translation, ...]:
    return (
        _Translation("en", en, en),
        _Translation("fr", fr, fr),
        _Translation("ar", ar, ar),
    )


def _finding(code: str, en: str, fr: str, ar: str) -> _ConceptSeed:
    return _ConceptSeed(
        code=code,
        kind="finding",
        narrative={
            "en": f"{{{{bodySite}}}}: {en}",
            "fr": f"{{{{bodySite}}}} : {fr}",
            "ar": f"{{{{bodySite}}}}: {ar}",
        },
        translations=_labels(en, fr, ar),
    )


def _procedure(code: str, en: str, fr: str, ar: str) -> _ConceptSeed:
    return _ConceptSeed(code=code, kind="procedure", translations=_labels(en, fr, ar))


def _drug(code: str, en: str, fr: str, ar: str) -> _ConceptSeed:
    return _ConceptSeed(code=code, kind="drug", translations=_labels(en, fr, ar))


_NEW_TM = (
    _finding(
        "FIND.TM.CHOLESTEATOMA", "Cholesteatoma", "Cholestéatome", "ورم كوليسترولي"
    ),
    _finding(
        "FIND.TM.TYMPANOSCLEROSIS",
        "Tympanosclerosis",
        "Tympanosclérose",
        "تصلب الطبلة",
    ),
    _finding(
        "FIND.TM.VENTILATION_TUBE",
        "Ventilation tube",
        "Aérateur transtympanique",
        "أنبوب تهوية",
    ),
    _finding("FIND.TM.NOT_VISUALIZED", "Not visualized", "Non visualisé", "غير مرئي"),
    _finding("FIND.TM.UNKNOWN", "Unknown", "Inconnu", "غير معروف"),
)
_NEW_CANAL = (
    _finding("FIND.CANAL.FOREIGN_BODY", "Foreign body", "Corps étranger", "جسم أجنبي"),
    _finding("FIND.CANAL.GRANULATION", "Granulation", "Granulation", "تحبب"),
    _finding("FIND.CANAL.EXOSTOSIS", "Exostosis", "Exostose", "عظم زائد"),
    _finding(
        "FIND.CANAL.NOT_VISUALIZED", "Not visualized", "Non visualisé", "غير مرئي"
    ),
    _finding("FIND.CANAL.UNKNOWN", "Unknown", "Inconnu", "غير معروف"),
)
_PROCEDURES = (
    _procedure("PROC.OTOSCOPY", "Otoscopy", "Otoscopie", "تنظير الأذن"),
    _procedure(
        "PROC.OTOMICROSCOPY", "Otomicroscopy", "Otomicroscopie", "فحص الأذن بالمجهر"
    ),
    _procedure(
        "PROC.CERUMEN_REMOVAL",
        "Cerumen removal",
        "Ablation de cérumen",
        "إزالة الصملاخ",
    ),
    _procedure(
        "PROC.EAR_FOREIGN_BODY",
        "Ear foreign-body removal",
        "Ablation d'un corps étranger de l'oreille",
        "إزالة جسم أجنبي من الأذن",
    ),
    _procedure("PROC.EAR_WICK", "Ear wick", "Mèche auriculaire", "فتيل أذني"),
    _procedure(
        "PROC.VENTILATION_TUBE",
        "Ventilation tube insertion",
        "Pose d'aérateur transtympanique",
        "وضع أنبوب تهوية",
    ),
    _procedure(
        "PROC.TUBE_REMOVAL",
        "Ventilation tube removal",
        "Ablation d'aérateur",
        "نزع أنبوب التهوية",
    ),
    _procedure(
        "PROC.INTRATYMPANIC_INJECTION",
        "Intratympanic injection",
        "Injection intratympanique",
        "حقن داخل الطبلة",
    ),
    _procedure(
        "PROC.CAVITY_CLEANING",
        "Mastoid cavity cleaning",
        "Nettoyage de cavité mastoïdienne",
        "تنظيف الجوف الخشائي",
    ),
)
_DRUGS = (
    _drug("DRUG.IT.DEXAMETHASONE", "Dexamethasone", "Dexaméthasone", "ديكساميثازون"),
    _drug(
        "DRUG.IT.METHYLPREDNISOLONE",
        "Methylprednisolone",
        "Méthylprednisolone",
        "ميثيل بريدنيزولون",
    ),
    _drug("DRUG.IT.GENTAMICIN", "Gentamicin", "Gentamicine", "جنتاميسين"),
)


async def seed_otology(
    session: AsyncSession,
    system: CodeSystem,
    by_code: dict[str, Concept],
) -> TerminologySeedReport:
    concepts_created = 0
    translations_created = 0
    for index, seed in enumerate((*_NEW_TM, *_NEW_CANAL, *_PROCEDURES, *_DRUGS)):
        concept, created = await _ensure_concept(
            session,
            system=system,
            seed=seed,
            sort_order=4000 + index,
            parent_id=None,
        )
        by_code[seed.code] = concept
        if created:
            concepts_created += 1
        translations_created += await _ensure_translations(
            session, concept, seed.translations
        )
    value_sets = 0
    members = 0
    tm_set, _created = await _ensure_value_set(session)
    canal_set, canal_created = await _ensure_coded_value_set(
        session,
        code="tm.canal.findings",
        name_key="terminology.valueSet.tmCanalFindings",
        description_key="terminology.valueSet.tmCanalFindings.description",
    )
    if canal_created:
        value_sets += 1
    catalogs = (
        (
            tm_set,
            (
                TM_NORMAL,
                *sorted(TM_ABNORMAL),
                TM_NOT_VISUALIZED,
                TM_UNKNOWN,
            ),
        ),
        (
            canal_set,
            (
                CANAL_NORMAL,
                *sorted(CANAL_ABNORMAL),
                CANAL_NOT_VISUALIZED,
                CANAL_UNKNOWN,
            ),
        ),
    )
    for value_set, codes in catalogs:
        for index, code in enumerate(codes):
            member = by_code.get(code)
            if member is None:
                continue
            members += await _ensure_member(
                session,
                value_set=value_set,
                concept=member,
                sort_order=index,
                is_default=code in {TM_NORMAL, CANAL_NORMAL},
            )
    procedure_set, created = await _ensure_coded_value_set(
        session,
        code="otology.procedures",
        name_key="terminology.valueSet.otologyProcedures",
        description_key="terminology.valueSet.otologyProcedures.description",
    )
    if created:
        value_sets += 1
    for index, code in enumerate(
        (
            PROC_OTOSCOPY,
            PROC_MICROSCOPY,
            PROC_WAX,
            PROC_FOREIGN_BODY,
            PROC_WICK,
            PROC_TUBE,
            PROC_TUBE_REMOVAL,
            PROC_INJECTION,
            PROC_CAVITY,
        )
    ):
        members += await _ensure_member(
            session,
            value_set=procedure_set,
            concept=by_code[code],
            sort_order=index,
            is_default=False,
        )
    drug_set, created = await _ensure_coded_value_set(
        session,
        code="otology.it_drugs",
        name_key="terminology.valueSet.otologyItDrugs",
        description_key="terminology.valueSet.otologyItDrugs.description",
    )
    if created:
        value_sets += 1
    for index, code in enumerate(IT_DRUGS):
        members += await _ensure_member(
            session,
            value_set=drug_set,
            concept=by_code[code],
            sort_order=index,
            is_default=False,
        )
    return TerminologySeedReport(
        code_systems=0,
        concepts=concepts_created,
        translations=translations_created,
        value_sets=value_sets,
        members=members,
    )
