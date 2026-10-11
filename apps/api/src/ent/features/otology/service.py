"""Otology use cases. Device tracking and recalls follow the saved procedure block."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.features.observations.repository import ObservationRepository
from ent.features.otology.assembly import present_devices, present_exams
from ent.features.otology.constants import (
    CLOSED_DEVICE_STATUSES,
    FLAG_CAVITY,
    FLAG_TUBE,
    PROC_MICROSCOPY,
    PROC_OTOSCOPY,
    PROCEDURE_BY_SUBTYPE,
)
from ent.features.otology.exceptions import (
    EarDeviceNotFoundError,
    OtologyNotFoundError,
    OtologyVersionConflictError,
)
from ent.features.otology.findings import build_observations
from ent.features.otology.mapping import to_page
from ent.features.otology.models import OfficeProcedure, OtologyExam
from ent.features.otology.repository import (
    EarDeviceRepository,
    OfficeProcedureRepository,
    OtologyRepository,
    ProcedureRecallRepository,
)
from ent.features.otology.rules import validate_exam
from ent.features.otology.schedule import (
    cancel_tube_recalls,
    clinic_today,
    end_matching_flags,
    load_plan,
    performed_on,
    reconcile,
)
from ent.features.otology.schemas.requests import (
    EarDeviceStatusUpdate,
    OtologyCreate,
    OtologyUpdate,
)
from ent.features.otology.schemas.responses import EarDeviceRead, OtologyExamRead
from ent.features.patients.repository import PatientFlagRepository
from ent.features.procedures.exceptions import ProcedureRecordNotFoundError
from ent.features.procedures.mapping import blank_to_none, to_utc_naive
from ent.features.procedures.models import ProcedureRecord
from ent.features.procedures.references import ProcedureReferences
from ent.features.procedures.repository import ProcedureRecordRepository
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository

Write = OtologyCreate | OtologyUpdate


class OtologyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = ProcedureReferences(session)

    async def create_exam(
        self,
        *,
        user: CurrentUser,
        body: OtologyCreate,
        content_locale: str,
    ) -> OtologyExamRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        validate_exam(body)
        concepts = await self._concepts(user, body)
        procedure = ProcedureRecord(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(patient.id),
            ),
            procedure_concept_id=int(concepts[_procedure_code(body)].id),
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
        await self._persist(user, procedure, exam, body, concepts)
        return await self._present_one(user, exam.public_id, content_locale)

    async def update_exam(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: OtologyUpdate,
        content_locale: str,
    ) -> OtologyExamRead:
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
        procedure.procedure_concept_id = int(concepts[_procedure_code(body)].id)
        procedure.performed_at = to_utc_naive(body.performed_at)
        procedure.laterality = body.laterality.value
        procedure.anesthesia = body.anesthesia
        procedure.setting = body.setting
        procedure.instrument = blank_to_none(body.instrument)
        procedure.indication_text = blank_to_none(body.indication_text)
        procedure.tolerance = body.tolerance
        procedure.updated_by_id = user.user_id
        _apply_exam(exam, body, user.user_id)
        exam.version = int(exam.version) + 1
        await self._persist(user, procedure, exam, body, concepts)
        return await self._present_one(user, exam.public_id, content_locale)

    async def get_exam(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> OtologyExamRead:
        self._bind(user)
        exam = await self._require(user, public_id)
        payload = await present_exams(
            self._session, self._refs, user, [exam], content_locale
        )
        self._access(user, exam, "get")
        await self._session.commit()
        return payload[0]

    async def get_for_procedure(
        self,
        *,
        user: CurrentUser,
        procedure_public_id: str,
        content_locale: str,
    ) -> OtologyExamRead:
        self._bind(user)
        procedure = await self._procedures(user).get_detail(procedure_public_id)
        if procedure is None:
            raise ProcedureRecordNotFoundError(public_id=procedure_public_id)
        await self._refs.assert_patient_visible(user, int(procedure.patient_id))
        exam = await self._exams(user).get_for_procedure(procedure_public_id)
        if exam is None:
            raise OtologyNotFoundError()
        payload = await present_exams(
            self._session, self._refs, user, [exam], content_locale
        )
        self._access(user, exam, "get")
        await self._session.commit()
        return payload[0]

    async def list_for_patient(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
        content_locale: str,
    ) -> PageSchema[OtologyExamRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        listed = await self._exams(user).list_for_patient(int(patient.id), page)
        items = await present_exams(
            self._session, self._refs, user, list(listed.items), content_locale
        )
        self._audit.record_access(
            action="list",
            entity_type="otology_exam",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        await self._session.commit()
        return to_page(
            items, total=listed.total, limit=listed.limit, offset=listed.offset
        )

    async def list_devices(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
    ) -> PageSchema[EarDeviceRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        listed = await self._devices(user).list_for_patient(int(patient.id), page)
        items = await present_devices(self._session, user, list(listed.items))
        self._audit.record_access(
            action="list",
            entity_type="ear_device",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        await self._session.commit()
        return to_page(
            items, total=listed.total, limit=listed.limit, offset=listed.offset
        )

    async def update_device_status(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: EarDeviceStatusUpdate,
    ) -> EarDeviceRead:
        self._bind(user)
        row = await self._devices(user).get_detail(public_id)
        if row is None:
            raise EarDeviceNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        if int(row.version) != body.version:
            raise OtologyVersionConflictError(
                server_version=int(row.version),
                client_version=body.version,
            )
        row.status = body.status
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        if body.status in CLOSED_DEVICE_STATUSES and row.removed_at is None:
            on = await clinic_today(self._session, user)
            row.removed_at = on
            flags = await PatientFlagRepository(
                self._session, clinic_id=user.clinic_id
            ).list_active(flag_code=None, patient_id=int(row.patient_id), limit=200)
            code = FLAG_TUBE if row.device_type == "ventilation_tube" else FLAG_CAVITY
            end_matching_flags(flags, code, row.laterality, on, user.user_id)
            if row.device_type == "ventilation_tube":
                await cancel_tube_recalls(
                    ProcedureRecallRepository(self._session, clinic_id=user.clinic_id),
                    int(row.patient_id),
                    row.laterality,
                    user.user_id,
                )
        presented = await present_devices(self._session, user, [row])
        return presented[0]

    async def _persist(
        self,
        user: CurrentUser,
        procedure: ProcedureRecord,
        exam: OtologyExam,
        body: Write,
        concepts: dict[str, Concept],
    ) -> None:
        del exam
        observations = self._observations(user)
        for row in await observations.list_for_procedure(int(procedure.id)):
            await observations.mark_deleted(row, user.user_id)
        for row in build_observations(
            clinic_id=user.clinic_id,
            patient_id=int(procedure.patient_id),
            procedure_record_id=int(procedure.id),
            encounter_id=procedure.encounter_id,
            encounter_public_id=body.encounter_public_id,
            user_id=user.user_id,
            effective_at=procedure.performed_at,
            body=body,
            concepts=concepts,
        ):
            await observations.add(row)
        office = await self._save_office(user, procedure, body)
        await reconcile(
            self._session,
            user,
            procedure,
            office,
            body,
            await load_plan(self._session, user),
            await performed_on(self._session, user, procedure),
        )

    async def _save_office(
        self,
        user: CurrentUser,
        procedure: ProcedureRecord,
        body: Write,
    ) -> OfficeProcedure | None:
        repo = OfficeProcedureRepository(self._session, clinic_id=user.clinic_id)
        existing = await repo.get_for_procedure(int(procedure.id))
        if body.procedure is None:
            if existing is not None:
                now = datetime.now(UTC).replace(tzinfo=None)
                existing.deleted_at = now
                existing.deleted_by_id = user.user_id
                existing.updated_by_id = user.user_id
            return None
        payload = body.procedure.model_dump(mode="json")
        if existing is None:
            row = OfficeProcedure(
                clinic_id=user.clinic_id,
                procedure_record_id=int(procedure.id),
                subtype=body.procedure.subtype,
                payload=payload,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            await repo.add(row)
            return row
        existing.subtype = body.procedure.subtype
        existing.payload = payload
        existing.updated_by_id = user.user_id
        existing.version = int(existing.version) + 1
        existing.deleted_at = None
        existing.deleted_by_id = None
        return existing

    async def _present_one(
        self,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> OtologyExamRead:
        await self._session.flush()
        self._session.expire_all()
        exam = await self._require(user, public_id)
        presented = await present_exams(
            self._session, self._refs, user, [exam], content_locale
        )
        return presented[0]

    async def _concepts(self, user: CurrentUser, body: Write) -> dict[str, Concept]:
        codes = {_procedure_code(body)}
        for item in body.structures:
            codes.add(item.body_site_code)
            codes.add(item.finding_code)
        block = body.procedure
        if block is not None and block.subtype == "intratympanic_injection":
            codes.add(block.drug_code)
        found = await self._terms(user).list_concepts_by_codes(sorted(codes))
        by_code = {row.code: row for row in found}
        missing = codes - set(by_code)
        if missing:
            raise ValidationError(reason="concept_missing", code=sorted(missing)[0])
        chosen = by_code[_procedure_code(body)]
        if chosen.kind != "procedure":
            raise ValidationError(reason="procedure_concept_kind", code=chosen.code)
        return by_code

    async def _require(self, user: CurrentUser, public_id: str) -> OtologyExam:
        exam = await self._exams(user).get_detail(public_id)
        if exam is None:
            raise OtologyNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(
            user, int(exam.procedure_record.patient_id)
        )
        return exam

    def _check_version(self, exam: OtologyExam, version: int) -> None:
        if int(exam.version) != version:
            raise OtologyVersionConflictError(
                server_version=int(exam.version),
                client_version=version,
            )

    def _access(self, user: CurrentUser, exam: OtologyExam, action: str) -> None:
        self._audit.record_access(
            action=action,
            entity_type="otology_exam",
            clinic_id=user.clinic_id,
            entity_id=int(exam.id),
            entity_public_id=exam.public_id,
            patient_id=int(exam.procedure_record.patient_id),
        )

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _exams(self, user: CurrentUser) -> OtologyRepository:
        return OtologyRepository(self._session, clinic_id=user.clinic_id)

    def _devices(self, user: CurrentUser) -> EarDeviceRepository:
        return EarDeviceRepository(self._session, clinic_id=user.clinic_id)

    def _procedures(self, user: CurrentUser) -> ProcedureRecordRepository:
        return ProcedureRecordRepository(self._session, clinic_id=user.clinic_id)

    def _observations(self, user: CurrentUser) -> ObservationRepository:
        return ObservationRepository(self._session, clinic_id=user.clinic_id)

    def _terms(self, user: CurrentUser) -> TerminologyRepository:
        return TerminologyRepository(self._session, clinic_id=user.clinic_id)


def _procedure_code(body: Write) -> str:
    if body.procedure is not None:
        return PROCEDURE_BY_SUBTYPE[body.procedure.subtype]
    if body.method == "microscopy":
        return PROC_MICROSCOPY
    return PROC_OTOSCOPY


def _exam(clinic_id: int, procedure_id: int, user_id: int, body: Write) -> OtologyExam:
    row = OtologyExam(
        clinic_id=clinic_id,
        procedure_record_id=procedure_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    _apply_exam(row, body, user_id)
    return row


def _apply_exam(exam: OtologyExam, body: Write, user_id: int) -> None:
    exam.method = body.method
    exam.weber = body.weber
    exam.rinne_right = body.rinne_right
    exam.rinne_left = body.rinne_left
    exam.fork_frequency_hz = body.fork_frequency_hz
    exam.mobility_right = body.mobility_right
    exam.mobility_left = body.mobility_left
    exam.conclusion_text = blank_to_none(body.conclusion_text)
    exam.updated_by_id = user_id
