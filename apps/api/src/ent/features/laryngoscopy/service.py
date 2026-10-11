"""Laryngoscopy use cases. Scores are recomputed from observations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.features.laryngoscopy.assembly import present_exams, store_scores
from ent.features.laryngoscopy.constants import (
    GRBAS_CONCEPT_CODES,
    PAS_CODE,
    PROCEDURE_CODE,
    RFS_CONCEPT_CODES,
    VF_SURFACES,
    VF_THIRDS,
    VOCAL_FOLD_CODE,
)
from ent.features.laryngoscopy.exceptions import (
    LaryngoscopyNotFoundError,
    LaryngoscopyVersionConflictError,
)
from ent.features.laryngoscopy.findings import build_observations
from ent.features.laryngoscopy.mapping import to_page
from ent.features.laryngoscopy.models import LaryngoscopyExam
from ent.features.laryngoscopy.repository import LaryngoscopyRepository
from ent.features.laryngoscopy.rules import validate_exam
from ent.features.laryngoscopy.schemas.requests import (
    LaryngoscopyCreate,
    LaryngoscopyUpdate,
)
from ent.features.laryngoscopy.schemas.responses import LaryngoscopyExamRead
from ent.features.laryngoscopy.scoring import LaryngoscopyScores, ScoreRow, compute
from ent.features.observations.models import Observation
from ent.features.observations.repository import ObservationRepository
from ent.features.procedures.exceptions import ProcedureRecordNotFoundError
from ent.features.procedures.mapping import blank_to_none, to_utc_naive
from ent.features.procedures.models import ProcedureRecord
from ent.features.procedures.references import ProcedureReferences
from ent.features.procedures.repository import ProcedureRecordRepository
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository

Write = LaryngoscopyCreate | LaryngoscopyUpdate


class LaryngoscopyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = ProcedureReferences(session)

    async def create_exam(
        self,
        *,
        user: CurrentUser,
        body: LaryngoscopyCreate,
        content_locale: str,
    ) -> LaryngoscopyExamRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        validate_exam(body)
        concepts = await self._concepts(user, body)
        encounter_id = await self._refs.encounter_id(
            user,
            body.encounter_public_id,
            patient_id=int(patient.id),
        )
        procedure = ProcedureRecord(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=encounter_id,
            procedure_concept_id=int(concepts[PROCEDURE_CODE].id),
            performed_at=to_utc_naive(body.performed_at),
            performed_by_id=user.user_id,
            laterality=body.laterality.value,
            anesthesia=body.anesthesia,
            setting=body.setting,
            instrument=blank_to_none(body.instrument),
            indication_text=blank_to_none(body.indication_text),
            tolerance=body.tolerance,
            status="draft",
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._procedures(user).add(procedure)
        exam = _exam(user.clinic_id, int(procedure.id), user.user_id, body)
        await self._exams(user).add(exam)
        await self._rewrite(user, procedure, exam, body, concepts)
        return await self._present_one(user, exam.public_id, content_locale)

    async def update_exam(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: LaryngoscopyUpdate,
        content_locale: str,
    ) -> LaryngoscopyExamRead:
        self._bind(user)
        exam = await self._require(user, public_id)
        procedure = exam.procedure_record
        self._procedures(user).assert_draft(procedure)
        self._check_version(exam, body.version)
        validate_exam(body)
        concepts = await self._concepts(user, body)
        procedure.encounter_id = await self._refs.encounter_id(
            user,
            body.encounter_public_id,
            patient_id=int(procedure.patient_id),
        )
        procedure.performed_at = to_utc_naive(body.performed_at)
        procedure.laterality = body.laterality.value
        procedure.anesthesia = body.anesthesia
        procedure.setting = body.setting
        procedure.instrument = blank_to_none(body.instrument)
        procedure.indication_text = blank_to_none(body.indication_text)
        procedure.tolerance = body.tolerance
        procedure.updated_by_id = user.user_id
        _apply_body(exam, body, user.user_id)
        exam.version = int(exam.version) + 1
        await self._rewrite(user, procedure, exam, body, concepts)
        return await self._present_one(user, exam.public_id, content_locale)

    async def get_exam(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> LaryngoscopyExamRead:
        self._bind(user)
        exam = await self._require(user, public_id)
        payload = await present_exams(
            self._session, self._refs, user, [exam], content_locale
        )
        self._audit.record_access(
            action="get",
            entity_type="laryngoscopy_exam",
            clinic_id=user.clinic_id,
            entity_id=int(exam.id),
            entity_public_id=exam.public_id,
            patient_id=int(exam.procedure_record.patient_id),
        )
        await self._session.commit()
        return payload[0]

    async def get_for_procedure(
        self,
        *,
        user: CurrentUser,
        procedure_public_id: str,
        content_locale: str,
    ) -> LaryngoscopyExamRead:
        self._bind(user)
        procedure = await self._procedures(user).get_detail(procedure_public_id)
        if procedure is None:
            raise ProcedureRecordNotFoundError(public_id=procedure_public_id)
        await self._refs.assert_patient_visible(user, int(procedure.patient_id))
        exam = await self._exams(user).get_for_procedure(procedure_public_id)
        if exam is None:
            raise LaryngoscopyNotFoundError()
        payload = await present_exams(
            self._session, self._refs, user, [exam], content_locale
        )
        self._audit.record_access(
            action="get",
            entity_type="laryngoscopy_exam",
            clinic_id=user.clinic_id,
            entity_id=int(exam.id),
            entity_public_id=exam.public_id,
            patient_id=int(procedure.patient_id),
        )
        await self._session.commit()
        return payload[0]

    async def list_for_patient(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
        content_locale: str,
    ) -> PageSchema[LaryngoscopyExamRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        listed = await self._exams(user).list_for_patient(int(patient.id), page)
        items = await present_exams(
            self._session, self._refs, user, list(listed.items), content_locale
        )
        self._audit.record_access(
            action="list",
            entity_type="laryngoscopy_exam",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        await self._session.commit()
        return to_page(
            items,
            total=listed.total,
            limit=listed.limit,
            offset=listed.offset,
        )

    async def _rewrite(
        self,
        user: CurrentUser,
        procedure: ProcedureRecord,
        exam: LaryngoscopyExam,
        body: Write,
        concepts: dict[str, Concept],
    ) -> None:
        observations = self._observations(user)
        existing = await observations.list_for_procedure(int(procedure.id))
        for row in existing:
            await observations.mark_deleted(row, user.user_id)
        built = build_observations(
            clinic_id=user.clinic_id,
            patient_id=int(procedure.patient_id),
            procedure_record_id=int(procedure.id),
            encounter_id=procedure.encounter_id,
            encounter_public_id=body.encounter_public_id,
            user_id=user.user_id,
            effective_at=procedure.performed_at,
            body=body,
            concepts=concepts,
        )
        for row in built:
            await observations.add(row)
        stored = await observations.list_for_procedure(int(procedure.id))
        by_id = {int(concept.id): concept for concept in concepts.values()}
        scores = compute(
            [_score_row(row, by_id) for row in stored],
            fees_performed=body.fees is not None,
        )
        _apply_scores(exam, scores)
        await store_scores(self._session, user, procedure, scores)

    async def _present_one(
        self,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> LaryngoscopyExamRead:
        await self._session.flush()
        self._session.expire_all()
        exam = await self._require(user, public_id)
        presented = await present_exams(
            self._session, self._refs, user, [exam], content_locale
        )
        return presented[0]

    async def _concepts(self, user: CurrentUser, body: Write) -> dict[str, Concept]:
        codes = _codes(body)
        found = await self._terms(user).list_concepts_by_codes(sorted(codes))
        by_code = {row.code: row for row in found}
        missing = codes - set(by_code)
        if missing:
            raise ValidationError(reason="concept_missing", code=sorted(missing)[0])
        procedure = by_code[PROCEDURE_CODE]
        if procedure.kind != "procedure":
            raise ValidationError(reason="procedure_concept_kind", code=PROCEDURE_CODE)
        return by_code

    async def _require(self, user: CurrentUser, public_id: str) -> LaryngoscopyExam:
        exam = await self._exams(user).get_detail(public_id)
        if exam is None:
            raise LaryngoscopyNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(
            user,
            int(exam.procedure_record.patient_id),
        )
        return exam

    def _check_version(self, exam: LaryngoscopyExam, version: int) -> None:
        if int(exam.version) != version:
            raise LaryngoscopyVersionConflictError(
                server_version=int(exam.version),
                client_version=version,
            )

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _exams(self, user: CurrentUser) -> LaryngoscopyRepository:
        return LaryngoscopyRepository(self._session, clinic_id=user.clinic_id)

    def _procedures(self, user: CurrentUser) -> ProcedureRecordRepository:
        return ProcedureRecordRepository(self._session, clinic_id=user.clinic_id)

    def _observations(self, user: CurrentUser) -> ObservationRepository:
        return ObservationRepository(self._session, clinic_id=user.clinic_id)

    def _terms(self, user: CurrentUser) -> TerminologyRepository:
        return TerminologyRepository(self._session, clinic_id=user.clinic_id)


def _codes(body: Write) -> set[str]:
    codes = {PROCEDURE_CODE}
    for item in body.structures:
        codes.add(item.body_site_code)
        codes.add(item.finding_code)
    if body.lesions:
        codes.add(VOCAL_FOLD_CODE)
        codes.update(VF_THIRDS)
        codes.update(VF_SURFACES)
    for lesion in body.lesions:
        codes.add(lesion.finding_code)
    if body.reflux_finding_score is not None:
        codes.update(RFS_CONCEPT_CODES.values())
    if body.grbas is not None:
        codes.update(GRBAS_CONCEPT_CODES.values())
    if body.fees is not None:
        codes.add(PAS_CODE)
        codes.update(body.fees.consistencies)
        if body.fees.residue_site_codes:
            codes.add("FIND.LARYNX.POOLING")
            codes.update(body.fees.residue_site_codes)
    return codes


def _exam(
    clinic_id: int,
    procedure_record_id: int,
    user_id: int,
    body: Write,
) -> LaryngoscopyExam:
    exam = LaryngoscopyExam(
        clinic_id=clinic_id,
        procedure_record_id=procedure_record_id,
        scope_type=body.scope_type,
        vf_mobility_right=body.vocal_fold_right.mobility,
        vf_mobility_left=body.vocal_fold_left.mobility,
        glottic_closure=body.glottic_closure,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    _apply_body(exam, body, user_id)
    return exam


def _apply_body(exam: LaryngoscopyExam, body: Write, user_id: int) -> None:
    exam.scope_type = body.scope_type
    exam.vf_mobility_right = body.vocal_fold_right.mobility
    exam.vf_mobility_left = body.vocal_fold_left.mobility
    exam.vf_position_right = body.vocal_fold_right.position
    exam.vf_position_left = body.vocal_fold_left.position
    exam.glottic_closure = body.glottic_closure
    exam.supraglottic_pattern = body.supraglottic_pattern
    exam.conclusion_text = blank_to_none(body.conclusion_text)
    exam.updated_by_id = user_id
    strobe = body.stroboscopy
    exam.stroboscopy_performed = strobe is not None
    exam.symmetry = strobe.symmetry if strobe is not None else None
    exam.periodicity = strobe.periodicity if strobe is not None else None
    exam.amplitude_right = strobe.amplitude_right if strobe is not None else None
    exam.amplitude_left = strobe.amplitude_left if strobe is not None else None
    exam.mucosal_wave_right = strobe.mucosal_wave_right if strobe is not None else None
    exam.mucosal_wave_left = strobe.mucosal_wave_left if strobe is not None else None
    exam.phase_closure = strobe.phase_closure if strobe is not None else None
    exam.phase_symmetry = strobe.phase_symmetry if strobe is not None else None
    exam.vertical_level = strobe.vertical_level if strobe is not None else None
    exam.non_vibrating_segment = (
        strobe.non_vibrating_segment if strobe is not None else None
    )
    exam.fees_performed = body.fees is not None


def _apply_scores(exam: LaryngoscopyExam, scores: LaryngoscopyScores) -> None:
    exam.rfs_score = scores.rfs_score
    exam.grbas_g = scores.grbas_g
    exam.grbas_r = scores.grbas_r
    exam.grbas_b = scores.grbas_b
    exam.grbas_a = scores.grbas_a
    exam.grbas_s = scores.grbas_s
    exam.pas_score = scores.pas_score


def _score_row(row: Observation, concepts: dict[int, Concept]) -> ScoreRow:
    concept = concepts.get(int(row.concept_id))
    return ScoreRow(
        concept_code=concept.code if concept is not None else "",
        ordinal_value=row.ordinal_value,
    )
