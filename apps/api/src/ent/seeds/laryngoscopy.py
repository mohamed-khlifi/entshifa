"""Laryngeal anatomy, vocal-fold lesions, and the laryngoscopy procedure.

# VERIFY: Arabic labels with a clinician before they appear on a signed report.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.laryngoscopy.constants import (
    CONSISTENCY_CODES,
    FINDING_CODES,
    GRBAS_CONCEPT_CODES,
    LESION_FINDINGS,
    PAS_CODE,
    PROCEDURE_CODE,
    RFS_CONCEPT_CODES,
    STRUCTURE_CODES,
    VF_SURFACES,
    VF_THIRDS,
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


_ANATOMY: tuple[tuple[str, str, str, str], ...] = (
    ("ANAT.LARYNX.VELUM", "Velum", "Voile du palais", "شراع الحنك"),
    ("ANAT.LARYNX.TONGUE_BASE", "Base of tongue", "Base de langue", "قاعدة اللسان"),
    ("ANAT.LARYNX.VALLECULA", "Vallecula", "Vallécule", "الوهدة"),
    ("ANAT.LARYNX.EPIGLOTTIS", "Epiglottis", "Épiglotte", "لسان المزمار"),
    (
        "ANAT.LARYNX.ARYEPIGLOTTIC_FOLD",
        "Aryepiglottic fold",
        "Pli aryépiglottique",
        "الطية الطرجهالية",
    ),
    ("ANAT.LARYNX.ARYTENOID", "Arytenoid", "Aryténoïde", "الطرجهالي"),
    ("ANAT.LARYNX.PYRIFORM", "Pyriform sinus", "Sinus piriforme", "الجيب الكمثري"),
    (
        "ANAT.LARYNX.POST_CRICOID",
        "Post-cricoid area",
        "Région rétro-cricoïdienne",
        "المنطقة خلف الحلقي",
    ),
    (
        "ANAT.LARYNX.FALSE_CORD",
        "False vocal fold",
        "Bande ventriculaire",
        "الوتر الكاذب",
    ),
    (
        "ANAT.LARYNX.VENTRICLE",
        "Laryngeal ventricle",
        "Ventricule laryngé",
        "بطين الحنجرة",
    ),
    ("ANAT.LARYNX.VOCAL_FOLD", "True vocal fold", "Corde vocale", "الوتر الصوتي"),
    (
        "ANAT.LARYNX.ANTERIOR_COMMISSURE",
        "Anterior commissure",
        "Commissure antérieure",
        "الصوار الأمامي",
    ),
    (
        "ANAT.LARYNX.POSTERIOR_COMMISSURE",
        "Posterior commissure",
        "Commissure postérieure",
        "الصوار الخلفي",
    ),
    ("ANAT.LARYNX.SUBGLOTTIS", "Subglottis", "Sous-glotte", "تحت المزمار"),
    ("ANAT.LARYNX.TRACHEA", "Upper trachea", "Trachée supérieure", "القصبة العلوية"),
    (
        "ANAT.LARYNX.VESTIBULE",
        "Laryngeal vestibule",
        "Vestibule laryngé",
        "دهليز الحنجرة",
    ),
)

_FINDING_LABELS: tuple[tuple[str, str, str, str], ...] = (
    ("FIND.LARYNX.NORMAL", "Normal", "Normal", "طبيعي"),
    ("FIND.LARYNX.EDEMA", "Edema", "Œdème", "وذمة"),
    ("FIND.LARYNX.ERYTHEMA", "Erythema", "Érythème", "احمرار"),
    ("FIND.LARYNX.SECRETIONS", "Secretions", "Sécrétions", "مفرزات"),
    ("FIND.LARYNX.POOLING", "Pooling", "Stase", "تجمع"),
    ("FIND.LARYNX.PACHYDERMIA", "Pachydermia", "Pachydermie", "ثخن مخاطي"),
    ("FIND.LARYNX.NOT_VISUALIZED", "Not visualized", "Non visualisé", "غير مرئي"),
    ("FIND.LARYNX.UNKNOWN", "Unknown", "Inconnu", "غير معروف"),
    ("FIND.LARYNX.NODULE", "Nodule", "Nodule", "عقيدة"),
    ("FIND.LARYNX.POLYP", "Polyp", "Polype", "سليلة"),
    ("FIND.LARYNX.CYST", "Cyst", "Kyste", "كيسة"),
    ("FIND.LARYNX.REINKE_EDEMA", "Reinke edema", "Œdème de Reinke", "وذمة راينكه"),
    ("FIND.LARYNX.GRANULOMA", "Granuloma", "Granulome", "ورم حبيبي"),
    ("FIND.LARYNX.PAPILLOMA", "Papilloma", "Papillome", "ورم حليمي"),
    ("FIND.LARYNX.LEUKOPLAKIA", "Leukoplakia", "Leucoplasie", "طلوان"),
    ("FIND.LARYNX.ERYTHROPLAKIA", "Erythroplakia", "Érythroplasie", "احمرار مخاطي"),
    ("FIND.LARYNX.ULCER", "Ulceration", "Ulcération", "تقرح"),
    ("FIND.LARYNX.MASS", "Mass", "Masse", "كتلة"),
    ("FIND.LARYNX.SULCUS", "Sulcus", "Sulcus", "تلم"),
    ("FIND.LARYNX.SCAR", "Scar", "Cicatrice", "ندبة"),
    ("FIND.LARYNX.WEB", "Web", "Bride", "غشاء"),
    ("FIND.LARYNX.VARIX", "Varix", "Varice", "دوالي"),
    ("FIND.LARYNX.HEMORRHAGE", "Hemorrhage", "Hémorragie", "نزيف"),
)

_QUALIFIERS: tuple[tuple[str, str, str, str], ...] = (
    ("QUAL.VF.THIRD.ANTERIOR", "Anterior third", "Tiers antérieur", "الثلث الأمامي"),
    ("QUAL.VF.THIRD.MIDDLE", "Middle third", "Tiers moyen", "الثلث الأوسط"),
    ("QUAL.VF.THIRD.POSTERIOR", "Posterior third", "Tiers postérieur", "الثلث الخلفي"),
    ("QUAL.VF.SURFACE.FREE_EDGE", "Free edge", "Bord libre", "الحافة الحرة"),
    ("QUAL.VF.SURFACE.SUPERIOR", "Superior surface", "Face supérieure", "السطح العلوي"),
)

_CONSISTENCY_LABELS: tuple[tuple[str, str, str, str], ...] = (
    ("FEES.CONSISTENCY.THIN", "Thin liquid", "Liquide clair", "سائل رقيق"),
    ("FEES.CONSISTENCY.NECTAR", "Nectar", "Nectar", "رحيق"),
    ("FEES.CONSISTENCY.HONEY", "Honey", "Miel", "عسل"),
    ("FEES.CONSISTENCY.PUREE", "Puree", "Purée", "مهروس"),
    ("FEES.CONSISTENCY.SOLID", "Solid", "Solide", "صلب"),
)


def _seeds() -> tuple[_ConceptSeed, ...]:
    rows: list[_ConceptSeed] = []
    for code, en, fr, ar in _ANATOMY:
        rows.append(
            _ConceptSeed(
                code=code,
                kind="anatomy",
                parent_code="ANAT.LARYNX",
                relationship="part_of",
                translations=_labels(en, fr, ar),
            )
        )
    for code, en, fr, ar in (*_FINDING_LABELS, *_QUALIFIERS, *_CONSISTENCY_LABELS):
        kind = (
            "qualifier"
            if code.startswith("QUAL.") or code.startswith("FEES.")
            else "finding"
        )
        rows.append(
            _ConceptSeed(code=code, kind=kind, translations=_labels(en, fr, ar))
        )
    for item, code in RFS_CONCEPT_CODES.items():
        rows.append(
            _ConceptSeed(
                code=code,
                kind="qualifier",
                translations=_labels(
                    item.replace("_", " "), item.replace("_", " "), item
                ),
                properties={"scorable": True, "rfs_item": item},
            )
        )
    for item, code in GRBAS_CONCEPT_CODES.items():
        rows.append(
            _ConceptSeed(
                code=code,
                kind="qualifier",
                translations=_labels(item, item, item),
                properties={"scorable": True, "grbas_item": item},
            )
        )
    rows.append(
        _ConceptSeed(
            code=PAS_CODE,
            kind="qualifier",
            translations=_labels(
                "Penetration-Aspiration Scale",
                "Échelle de pénétration-aspiration",
                "مقياس الاختراق والاستنشاق",
            ),
            properties={"scorable": True},
        )
    )
    rows.append(
        _ConceptSeed(
            code=PROCEDURE_CODE,
            kind="procedure",
            translations=_labels(
                "Fiberoptic laryngoscopy",
                "Laryngoscopie fibroscopique",
                "تنظير الحنجرة",
            ),
        )
    )
    return tuple(rows)


async def seed_laryngoscopy(
    session: AsyncSession,
    system: CodeSystem,
    by_code: dict[str, Concept],
) -> TerminologySeedReport:
    concepts_created = 0
    translations_created = 0
    for index, seed in enumerate(_seeds()):
        parent = by_code.get(seed.parent_code) if seed.parent_code else None
        concept, created = await _ensure_concept(
            session,
            system=system,
            seed=seed,
            sort_order=3000 + index,
            parent_id=parent.id if parent else None,
        )
        by_code[seed.code] = concept
        if created:
            concepts_created += 1
        if parent is not None and seed.relationship is not None:
            await _ensure_relationship(
                session,
                source=concept,
                target=parent,
                rel_type=seed.relationship,
            )
        translations_created += await _ensure_translations(
            session, concept, seed.translations
        )
    value_sets = 0
    members = 0
    catalogs = (
        ("laryngoscopy.structures", STRUCTURE_CODES),
        ("laryngoscopy.findings", tuple(sorted(FINDING_CODES))),
        ("laryngoscopy.lesions", tuple(sorted(LESION_FINDINGS))),
        ("laryngoscopy.vf_thirds", VF_THIRDS),
        ("laryngoscopy.vf_surfaces", VF_SURFACES),
        ("fees.consistencies", CONSISTENCY_CODES),
    )
    for code, members_codes in catalogs:
        value_set, created = await _ensure_coded_value_set(
            session,
            code=code,
            name_key=f"terminology.valueSet.{code}",
            description_key=f"terminology.valueSet.{code}.description",
        )
        if created:
            value_sets += 1
        for index, member_code in enumerate(members_codes):
            if member_code not in by_code:
                continue
            members += await _ensure_member(
                session,
                value_set=value_set,
                concept=by_code[member_code],
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
