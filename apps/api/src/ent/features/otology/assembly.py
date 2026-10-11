"""Load the rows an otology read model is built from."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.principal import CurrentUser
from ent.features.observations.models import Observation
from ent.features.observations.repository import ObservationRepository
from ent.features.otology.mapping import to_device_read, to_exam_read
from ent.features.otology.models import EarDevice, OtologyExam
from ent.features.otology.repository import (
    EarDeviceRepository,
    OfficeProcedureRepository,
)
from ent.features.otology.schemas.responses import EarDeviceRead, OtologyExamRead
from ent.features.procedures.references import ProcedureReferences
from ent.features.procedures.repository import ProcedureRecordRepository
from ent.features.terminology.repository import TerminologyRepository


async def present_exams(
    session: AsyncSession,
    refs: ProcedureReferences,
    user: CurrentUser,
    exams: list[OtologyExam],
    content_locale: str,
) -> list[OtologyExamRead]:
    if not exams:
        return []
    procedure_ids = [int(exam.procedure_record_id) for exam in exams]
    observations = await ObservationRepository(
        session, clinic_id=user.clinic_id
    ).list_for_procedures(procedure_ids)
    grouped: dict[int, list[Observation]] = {key: [] for key in procedure_ids}
    concept_ids: set[int] = set()
    for observation in observations:
        procedure_id = observation.procedure_record_id
        if procedure_id is None:
            continue
        grouped[int(procedure_id)].append(observation)
        concept_ids.add(int(observation.concept_id))
        if observation.body_site_concept_id is not None:
            concept_ids.add(int(observation.body_site_concept_id))
    concepts = {
        int(row.id): row
        for row in await TerminologyRepository(
            session, clinic_id=user.clinic_id
        ).list_concepts_by_ids(concept_ids)
    }
    labels = await refs.labels(user, concept_ids, content_locale)
    offices = {
        int(row.procedure_record_id): row
        for row in await OfficeProcedureRepository(
            session, clinic_id=user.clinic_id
        ).list_for_procedures(procedure_ids)
    }
    devices = await EarDeviceRepository(
        session, clinic_id=user.clinic_id
    ).list_for_inserted_procedures(procedure_ids)
    device_groups: dict[int, list[EarDevice]] = {key: [] for key in procedure_ids}
    inserted_ids: set[int] = set()
    for device in devices:
        if device.inserted_procedure_id is None:
            continue
        device_groups[int(device.inserted_procedure_id)].append(device)
        inserted_ids.add(int(device.inserted_procedure_id))
    public_ids = await ProcedureRecordRepository(
        session, clinic_id=user.clinic_id
    ).public_ids_by_id(inserted_ids)
    return [
        to_exam_read(
            exam,
            grouped.get(int(exam.procedure_record_id), []),
            concepts,
            labels,
            offices.get(int(exam.procedure_record_id)),
            device_groups.get(int(exam.procedure_record_id), []),
            public_ids,
        )
        for exam in exams
    ]


async def present_devices(
    session: AsyncSession,
    user: CurrentUser,
    devices: list[EarDevice],
) -> list[EarDeviceRead]:
    inserted = {
        int(row.inserted_procedure_id)
        for row in devices
        if row.inserted_procedure_id is not None
    }
    public_ids = await ProcedureRecordRepository(
        session, clinic_id=user.clinic_id
    ).public_ids_by_id(inserted)
    return [to_device_read(row, public_ids) for row in devices]
