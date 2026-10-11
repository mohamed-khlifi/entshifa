"""Map otology rows to read models."""

from __future__ import annotations

from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import CodeableConcept
from ent.features.observations.models import Observation
from ent.features.otology.models import EarDevice, OfficeProcedure, OtologyExam
from ent.features.otology.schemas.responses import (
    EarDeviceRead,
    OfficeProcedureRead,
    OtologyExamRead,
    OtologyStructureRead,
)
from ent.features.terminology.models import Concept

_LABELS = dict[int, tuple[str, str, str | None]]


def to_exam_read(
    exam: OtologyExam,
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
    office: OfficeProcedure | None,
    devices: list[EarDevice],
    procedure_public_ids: dict[int, str],
) -> OtologyExamRead:
    procedure = exam.procedure_record
    encounter = procedure.encounter
    return OtologyExamRead(
        public_id=exam.public_id,
        version=int(exam.version),
        procedure_id=procedure.public_id,
        procedure_status=procedure.status,
        procedure_code=procedure.procedure_concept.code,
        patient_id=procedure.patient.public_id,
        encounter_id=encounter.public_id if encounter is not None else None,
        performed_at=procedure.performed_at,
        laterality=procedure.laterality,
        anesthesia=procedure.anesthesia,
        setting=procedure.setting,
        instrument=procedure.instrument,
        indication_text=procedure.indication_text,
        tolerance=procedure.tolerance,
        method=exam.method,
        weber=exam.weber,
        rinne_right=exam.rinne_right,
        rinne_left=exam.rinne_left,
        fork_frequency_hz=exam.fork_frequency_hz,
        mobility_right=exam.mobility_right,
        mobility_left=exam.mobility_left,
        structures=_structures(observations, concepts, labels),
        procedure=_office(office),
        devices=[_device(row, procedure_public_ids) for row in devices],
        conclusion_text=exam.conclusion_text,
        created_at=exam.created_at,
        updated_at=exam.updated_at,
    )


def to_device_read(
    row: EarDevice, procedure_public_ids: dict[int, str]
) -> EarDeviceRead:
    return _device(row, procedure_public_ids)


def to_page[T](
    items: list[T],
    *,
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[T]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset, next_cursor=None),
    )


def _office(row: OfficeProcedure | None) -> OfficeProcedureRead | None:
    if row is None:
        return None
    payload = {
        str(key): None if value is None else str(value)
        for key, value in dict(row.payload).items()
    }
    return OfficeProcedureRead(
        subtype=row.subtype,
        payload=payload,
        removal_due_date=row.removal_due_date,
    )


def _device(row: EarDevice, procedure_public_ids: dict[int, str]) -> EarDeviceRead:
    inserted = row.inserted_procedure_id
    return EarDeviceRead(
        public_id=row.public_id,
        version=int(row.version),
        laterality=row.laterality,
        device_type=row.device_type,
        tube_model=row.tube_model,
        status=row.status,
        inserted_at=row.inserted_at,
        removed_at=row.removed_at,
        next_check_due=row.next_check_due,
        complication=row.complication,
        inserted_procedure_id=(
            procedure_public_ids.get(int(inserted)) if inserted is not None else None
        ),
    )


def _structures(
    observations: list[Observation],
    concepts: dict[int, Concept],
    labels: _LABELS,
) -> list[OtologyStructureRead]:
    rows: list[OtologyStructureRead] = []
    for observation in observations:
        if observation.body_site_concept_id is None:
            continue
        finding = concepts.get(int(observation.concept_id))
        site = concepts.get(int(observation.body_site_concept_id))
        if finding is None or site is None:
            continue
        rows.append(
            OtologyStructureRead(
                body_site=_concept(int(site.id), site, labels),
                laterality=str(observation.laterality),
                status=observation.status,
                finding=_concept(int(finding.id), finding, labels),
                map_region_code=observation.map_region_code,
            )
        )
    return rows


def _concept(concept_id: int, concept: Concept, labels: _LABELS) -> CodeableConcept:
    labeled = labels.get(concept_id)
    if labeled is None:
        return CodeableConcept(concept_id=concept.public_id, code=concept.code)
    public_id, code, display = labeled
    return CodeableConcept(concept_id=public_id, code=code, display=display)
