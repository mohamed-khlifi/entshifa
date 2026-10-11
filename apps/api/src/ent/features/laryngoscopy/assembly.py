"""Load and store the rows a laryngoscopy read model is built from."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.laryngoscopy.constants import VF_SURFACES, VF_THIRDS
from ent.features.laryngoscopy.mapping import to_exam_read
from ent.features.laryngoscopy.models import LaryngoscopyExam
from ent.features.laryngoscopy.schemas.responses import LaryngoscopyExamRead
from ent.features.laryngoscopy.scoring import LaryngoscopyScores
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
    exams: list[LaryngoscopyExam],
    content_locale: str,
) -> list[LaryngoscopyExamRead]:
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
    terms = TerminologyRepository(session, clinic_id=user.clinic_id)
    extra = await terms.list_concepts_by_codes([*VF_THIRDS, *VF_SURFACES])
    concepts = {
        int(row.id): row for row in await terms.list_concepts_by_ids(concept_ids)
    }
    for row in extra:
        concepts[int(row.id)] = row
        concept_ids.add(int(row.id))
    by_code = {row.code: row for row in concepts.values()}
    labels = await refs.labels(user, concept_ids, content_locale)
    calculations = await CalculationResultRepository(
        session, clinic_id=user.clinic_id
    ).list_for_procedures(procedure_ids)
    calc_grouped: dict[int, list[CalculationResultRow]] = {
        key: [] for key in procedure_ids
    }
    for calculation in calculations:
        if calculation.procedure_record_id is not None:
            calc_grouped[int(calculation.procedure_record_id)].append(calculation)
    return [
        to_exam_read(
            exam,
            grouped.get(int(exam.procedure_record_id), []),
            concepts,
            by_code,
            labels,
            calc_grouped.get(int(exam.procedure_record_id), []),
        )
        for exam in exams
    ]


async def store_scores(
    session: AsyncSession,
    user: CurrentUser,
    procedure: ProcedureRecord,
    scores: LaryngoscopyScores,
) -> None:
    """Append calculator rows. Older rows stay so a later version remains reproducible."""

    now = datetime.now(UTC).replace(tzinfo=None)
    repository = CalculationResultRepository(session, clinic_id=user.clinic_id)
    for result in (
        scores.reflux_finding_score,
        scores.grbas,
        scores.penetration_aspiration,
    ):
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
