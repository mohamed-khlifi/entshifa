"""Map a laryngoscopy exam and its observations to the API read model."""

from __future__ import annotations

from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import CodeableConcept
from ent.engines.registry import registered_calculators
from ent.features.laryngoscopy.constants import (
    CONSISTENCY_CODES,
    FINDING_CODES,
    LESION_FINDINGS,
    RFS_ITEM_BY_CODE,
    RFS_ITEMS,
    STRUCTURE_CODES,
)
from ent.features.laryngoscopy.models import LaryngoscopyExam
from ent.features.laryngoscopy.schemas.responses import (
    GrbasRead,
    LaryngoscopyExamRead,
    LaryngoscopyStructureRead,
    RefluxFindingScoreRead,
    ScoreStampRead,
    VocalFoldLesionRead,
    VocalFoldRead,
)
from ent.features.observations.models import Observation
from ent.features.prescriptions.models import CalculationResultRow
from ent.features.terminology.models import Concept

_LABELS = dict[int, tuple[str, str, str | None]]
_SIDE_ORDER = {"right": 0, "left": 1, "midline": 2, "na": 3, "bilateral": 4}
_FORMULAS = {spec.code: spec.formula for spec in registered_calculators()}
_CONSISTENCIES = frozenset(CONSISTENCY_CODES)
_SCORE_CODES = (
    "laryngoscopy.reflux_finding_score",
    "laryngoscopy.grbas",
    "laryngoscopy.penetration_aspiration",
)


def to_exam_read(
    exam: LaryngoscopyExam,
    observations: list[Observation],
    concepts: dict[int, Concept],
    by_code: dict[str, Concept],
    labels: _LABELS,
    calculations: list[CalculationResultRow],
) -> LaryngoscopyExamRead:
    procedure = exam.procedure_record
    encounter = procedure.encounter
    return LaryngoscopyExamRead(
        public_id=exam.public_id,
        version=int(exam.version),
        procedure_id=procedure.public_id,
        procedure_status=procedure.status,
        patient_id=procedure.patient.public_id,
        encounter_id=encounter.public_id if encounter is not None else None,
        performed_at=procedure.performed_at,
        laterality=procedure.laterality,
        anesthesia=procedure.anesthesia,
        setting=procedure.setting,
        instrument=procedure.instrument,
        indication_text=procedure.indication_text,
        tolerance=procedure.tolerance,
        scope_type=exam.scope_type,
        vocal_fold_right=VocalFoldRead(
            mobility=exam.vf_mobility_right,
            position=exam.vf_position_right,
        ),
        vocal_fold_left=VocalFoldRead(
            mobility=exam.vf_mobility_left,
            position=exam.vf_position_left,
        ),
        glottic_closure=exam.glottic_closure,
        supraglottic_pattern=exam.supraglottic_pattern,
        stroboscopy_performed=bool(exam.stroboscopy_performed),
        symmetry=exam.symmetry,
        periodicity=exam.periodicity,
        amplitude_right=exam.amplitude_right,
        amplitude_left=exam.amplitude_left,
        mucosal_wave_right=exam.mucosal_wave_right,
        mucosal_wave_left=exam.mucosal_wave_left,
        phase_closure=exam.phase_closure,
        phase_symmetry=exam.phase_symmetry,
        vertical_level=exam.vertical_level,
        non_vibrating_segment=exam.non_vibrating_segment,
        fees_performed=bool(exam.fees_performed),
        rfs_score=exam.rfs_score,
        reflux_finding_score=_rfs(observations, concepts),
        grbas=_grbas(exam),
        pas_score=exam.pas_score,
        consistencies=_coded_observations(
            observations, concepts, labels, _CONSISTENCIES
        ),
        residue_sites=_residue(observations, concepts, labels),
        structures=_structures(observations, concepts, labels),
        lesions=_lesions(observations, concepts, by_code, labels),
        scores=_stamps(exam, calculations),
        conclusion_text=exam.conclusion_text,
        created_at=exam.created_at,
        updated_at=exam.updated_at,
    )


def to_page(
    items: list[LaryngoscopyExamRead],
    *,
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[LaryngoscopyExamRead]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset, next_cursor=None),
    )


def _rfs(
    observations: list[Observation],
    concepts: dict[int, Concept],
) -> RefluxFindingScoreRead | None:
    grades: dict[str, int] = {}
    for observation in observations:
        concept = concepts.get(int(observation.concept_id))
        if concept is None or observation.ordinal_value is None:
            continue
        item = RFS_ITEM_BY_CODE.get(concept.code)
        if item is None:
            continue
        grades[item] = int(observation.ordinal_value)
    if any(item not in grades for item in RFS_ITEMS):
        return None
    return RefluxFindingScoreRead(
        subglottic_edema=grades["subglottic_edema"],
        ventricular_obliteration=grades["ventricular_obliteration"],
        erythema=grades["erythema"],
        vocal_fold_edema=grades["vocal_fold_edema"],
        diffuse_laryngeal_edema=grades["diffuse_laryngeal_edema"],
        posterior_commissure_hypertrophy=grades["posterior_commissure_hypertrophy"],
        granuloma=grades["granuloma"],
        thick_endolaryngeal_mucus=grades["thick_endolaryngeal_mucus"],
    )


def _grbas(exam: LaryngoscopyExam) -> GrbasRead | None:
    parts = (exam.grbas_g, exam.grbas_r, exam.grbas_b, exam.grbas_a, exam.grbas_s)
    if any(part is None for part in parts):
        return None
    values = [int(part) for part in parts if part is not None]
    return GrbasRead(
        grade=values[0],
        roughness=values[1],
        breathiness=values[2],
        asthenia=values[3],
        strain=values[4],
        total=sum(values),
    )


def _structures(
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
) -> list[LaryngoscopyStructureRead]:
    order = {code: index for index, code in enumerate(STRUCTURE_CODES)}
    rows: list[LaryngoscopyStructureRead] = []
    for observation in observations:
        finding = concepts.get(int(observation.concept_id))
        if finding is None or finding.code not in FINDING_CODES:
            continue
        if (observation.qualifiers or {}).get("role") == "residue":
            continue
        if observation.body_site_concept_id is None:
            continue
        site = concepts.get(int(observation.body_site_concept_id))
        if site is None or site.code not in order:
            continue
        rows.append(
            LaryngoscopyStructureRead(
                body_site=_coded(site, labels),
                laterality=str(observation.laterality),
                status=observation.status,
                finding=_coded(finding, labels),
            )
        )
    rows.sort(
        key=lambda item: (
            order.get(item.body_site.code or "", len(order)),
            _SIDE_ORDER.get(item.laterality, 9),
        )
    )
    return rows


def _lesions(
    observations: list[Observation],
    concepts: dict[int, Concept],
    by_code: dict[str, Concept],
    labels: _LABELS,
) -> list[VocalFoldLesionRead]:
    rows: list[VocalFoldLesionRead] = []
    for observation in observations:
        finding = concepts.get(int(observation.concept_id))
        if finding is None or finding.code not in LESION_FINDINGS:
            continue
        qualifiers = observation.qualifiers or {}
        third = by_code.get(str(qualifiers.get("third", "")))
        surface = by_code.get(str(qualifiers.get("surface", "")))
        if third is None or surface is None:
            continue
        size = qualifiers.get("sizeMm")
        grade = qualifiers.get("reinkeGrade")
        rows.append(
            VocalFoldLesionRead(
                laterality=str(observation.laterality),
                third=_coded(third, labels),
                surface=_coded(surface, labels),
                finding=_coded(finding, labels),
                size_mm=int(size) if isinstance(size, str) and size.isdigit() else None,
                reinke_grade=(
                    int(grade) if isinstance(grade, str) and grade.isdigit() else None
                ),
            )
        )
    return rows


def _coded_observations(
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
    allowed: frozenset[str],
) -> list[CodeableConcept]:
    rows: list[CodeableConcept] = []
    for observation in observations:
        concept = concepts.get(int(observation.concept_id))
        if concept is None or concept.code not in allowed:
            continue
        rows.append(_coded(concept, labels))
    return rows


def _residue(
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
) -> list[CodeableConcept]:
    rows: list[CodeableConcept] = []
    for observation in observations:
        if observation.map_region_code is None:
            continue
        finding = concepts.get(int(observation.concept_id))
        if finding is None or finding.code != "FIND.LARYNX.POOLING":
            continue
        if observation.body_site_concept_id is None:
            continue
        site = concepts.get(int(observation.body_site_concept_id))
        if site is None:
            continue
        rows.append(_coded(site, labels))
    return rows


def _stamps(
    exam: LaryngoscopyExam,
    calculations: list[CalculationResultRow],
) -> list[ScoreStampRead]:
    latest: dict[str, CalculationResultRow] = {}
    for row in calculations:
        latest.setdefault(row.calculator_code, row)
    visible: set[str] = set()
    if exam.rfs_score is not None:
        visible.add("laryngoscopy.reflux_finding_score")
    if exam.grbas_g is not None:
        visible.add("laryngoscopy.grbas")
    if exam.pas_score is not None:
        visible.add("laryngoscopy.penetration_aspiration")
    stamps: list[ScoreStampRead] = []
    for code in _SCORE_CODES:
        found = latest.get(code)
        if found is None or code not in visible:
            continue
        stamps.append(
            ScoreStampRead(
                code=found.calculator_code,
                version=found.engine_version,
                value=found.value,
                unit=found.unit,
                reference=found.reference,
                formula=_FORMULAS.get(found.calculator_code, ""),
            )
        )
    return stamps


def _coded(concept: Concept, labels: _LABELS) -> CodeableConcept:
    labeled = labels.get(int(concept.id))
    display = labeled[2] if labeled is not None else None
    return CodeableConcept(
        concept_id=concept.public_id,
        code=concept.code,
        display=display,
    )
