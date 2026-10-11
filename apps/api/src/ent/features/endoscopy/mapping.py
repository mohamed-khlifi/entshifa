"""Map an endoscopy exam and its observations to the API read model."""

from __future__ import annotations

from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import CodeableConcept
from ent.engines.registry import registered_calculators
from ent.features.endoscopy.constants import (
    ENDOSCOPY_STRUCTURE_CODES,
    FINDING_CODES,
    LK_ITEM_BY_CODE,
    LK_ITEMS,
)
from ent.features.endoscopy.exceptions import EndoscopyIncompleteScoreError
from ent.features.endoscopy.models import EndoscopyExam
from ent.features.endoscopy.schemas.responses import (
    EndoscopyExamRead,
    EndoscopyStructureRead,
    LundKennedySideRead,
    ScoreStampRead,
)
from ent.features.observations.models import Observation
from ent.features.prescriptions.models import CalculationResultRow
from ent.features.terminology.models import Concept

_LABELS = dict[int, tuple[str, str, str | None]]
_SIDE_ORDER = {"right": 0, "left": 1, "midline": 2, "na": 3, "bilateral": 4}
_FORMULAS = {spec.code: spec.formula for spec in registered_calculators()}


def to_exam_read(
    exam: EndoscopyExam,
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
    calculations: list[CalculationResultRow],
) -> EndoscopyExamRead:
    procedure = exam.procedure_record
    encounter = procedure.encounter
    return EndoscopyExamRead(
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
        decongestant_used=bool(exam.decongestant_used),
        lund_kennedy_right=_side(exam, observations, concepts, "right"),
        lund_kennedy_left=_side(exam, observations, concepts, "left"),
        lund_kennedy_total=int(exam.lund_kennedy_right) + int(exam.lund_kennedy_left),
        modified_lk_right=int(exam.modified_lk_right),
        modified_lk_left=int(exam.modified_lk_left),
        modified_lk_total=int(exam.modified_lk_right) + int(exam.modified_lk_left),
        polyp_grade_right=exam.polyp_grade_right,
        polyp_grade_left=exam.polyp_grade_left,
        polyp_scale=exam.polyp_scale,
        adenoid_obstruction_pct=exam.adenoid_obstruction_pct,
        conclusion_text=exam.conclusion_text,
        structures=_structures(observations, concepts, labels),
        scores=_stamps(exam, calculations),
        created_at=exam.created_at,
        updated_at=exam.updated_at,
    )


def to_page(
    items: list[EndoscopyExamRead],
    *,
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[EndoscopyExamRead]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset, next_cursor=None),
    )


def _side(
    exam: EndoscopyExam,
    observations: list[Observation],
    concepts: dict[int, Concept],
    side: str,
) -> LundKennedySideRead:
    values: dict[str, int] = {}
    for observation in observations:
        concept = concepts.get(int(observation.concept_id))
        if concept is None or observation.laterality != side:
            continue
        item = LK_ITEM_BY_CODE.get(concept.code)
        if item is None or observation.ordinal_value is None:
            continue
        values[item] = int(observation.ordinal_value)
    missing = [item for item in LK_ITEMS if item not in values]
    if missing:
        raise EndoscopyIncompleteScoreError(item=missing[0], side=side)
    total = (
        int(exam.lund_kennedy_right) if side == "right" else int(exam.lund_kennedy_left)
    )
    return LundKennedySideRead(
        polyps=values["polyps"],
        edema=values["edema"],
        discharge=values["discharge"],
        scarring=values["scarring"],
        crusting=values["crusting"],
        total=total,
    )


def _structures(
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
) -> list[EndoscopyStructureRead]:
    order = {code: index for index, code in enumerate(ENDOSCOPY_STRUCTURE_CODES)}
    rows: list[EndoscopyStructureRead] = []
    for observation in observations:
        finding = concepts.get(int(observation.concept_id))
        if finding is None or finding.code not in FINDING_CODES:
            continue
        if observation.body_site_concept_id is None:
            continue
        site = concepts.get(int(observation.body_site_concept_id))
        if site is None:
            continue
        rows.append(
            EndoscopyStructureRead(
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


def _stamps(
    exam: EndoscopyExam,
    calculations: list[CalculationResultRow],
) -> list[ScoreStampRead]:
    latest: dict[str, CalculationResultRow] = {}
    for row in calculations:
        latest.setdefault(row.calculator_code, row)
    visible = {
        "endoscopy.lund_kennedy",
        "endoscopy.modified_lund_kennedy",
    }
    if exam.polyp_grade_right is not None and exam.polyp_grade_left is not None:
        visible.add("endoscopy.polyp_grade")
    if exam.adenoid_obstruction_pct is not None:
        visible.add("endoscopy.adenoid_obstruction")
    stamps: list[ScoreStampRead] = []
    for code in (
        "endoscopy.lund_kennedy",
        "endoscopy.modified_lund_kennedy",
        "endoscopy.polyp_grade",
        "endoscopy.adenoid_obstruction",
    ):
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
