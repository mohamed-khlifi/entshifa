"""Load and store the rows an endoscopy read model is built from."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.endoscopy.mapping import to_exam_read
from ent.features.endoscopy.models import EndoscopyExam
from ent.features.endoscopy.schemas.responses import EndoscopyExamRead
from ent.features.endoscopy.scoring import EndoscopyScores
from ent.features.observations.models import Observation
from ent.features.observations.repository import ObservationRepository
from ent.features.prescriptions.models import CalculationResultRow
from ent.features.prescriptions.repository import CalculationResultRepository
from ent.features.procedures.models import ProcedureRecord
from ent.features.procedures.references import ProcedureReferences
from ent.features.terminology.repository import TerminologyRepository


async def present_exams(
    session: AsyncSession,
    refs: ProcedureReferences,
    user: CurrentUser,
    exams: list[EndoscopyExam],
    content_locale: str,
) -> list[EndoscopyExamRead]:
    """Resolve observations, concepts and the latest score stamps in one pass."""

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
    calculations = await CalculationResultRepository(
        session, clinic_id=user.clinic_id
    ).list_for_procedures(procedure_ids)
    calc_grouped: dict[int, list[CalculationResultRow]] = {
        key: [] for key in procedure_ids
    }
    for row in calculations:
        if row.procedure_record_id is not None:
            calc_grouped[int(row.procedure_record_id)].append(row)
    return [
        to_exam_read(
            exam,
            grouped.get(int(exam.procedure_record_id), []),
            concepts,
            labels,
            calc_grouped.get(int(exam.procedure_record_id), []),
        )
        for exam in exams
    ]


async def store_scores(
    session: AsyncSession,
    user: CurrentUser,
    procedure: ProcedureRecord,
    scores: EndoscopyScores,
) -> None:
    """Append calculator rows. Older rows stay so a later version remains reproducible."""

    now = datetime.now(UTC).replace(tzinfo=None)
    repository = CalculationResultRepository(session, clinic_id=user.clinic_id)
    results = (
        scores.lund_kennedy,
        scores.modified_lund_kennedy,
        scores.polyp_grade,
        scores.adenoid,
    )
    for result in results:
        if result is None:
            continue
        await repository.add(
            CalculationResultRow(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                patient_id=int(procedure.patient_id),
                encounter_id=procedure.encounter_id,
                procedure_record_id=int(procedure.id),
                calculator_code=result.code,
                engine_version=result.version,
                inputs=dict(result.inputs),
                value=result.value,
                unit=result.unit,
                flags=[
                    {"code": flag.code, "detail": dict(flag.detail)}
                    for flag in result.flags
                ],
                reference=result.reference,
                computed_at=now,
                computed_by_id=user.user_id,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
