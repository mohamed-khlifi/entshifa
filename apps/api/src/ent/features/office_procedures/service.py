"""Short office-procedure use cases. Signing stays on the parent record."""

from __future__ import annotations

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.schemas.common import CodeableConcept
from ent.core.security.principal import CurrentUser
from ent.features.clinics.repository import ClinicRepository
from ent.features.office_procedures.constants import PROCEDURE_BY_SUBTYPE
from ent.features.office_procedures.exceptions import (
    OfficeProcedureInvalidError,
    OfficeProcedureNotFoundError,
    OfficeProcedureVersionConflictError,
)
from ent.features.office_procedures.repository import ShortOfficeProcedureRepository
from ent.features.office_procedures.schedule import (
    dates_before_procedure,
    removal_due_date,
    result_due_date,
)
from ent.features.office_procedures.schemas.requests import (
    OfficeProcedureCreate,
    OfficeProcedureUpdate,
    ShortProcedureWrite,
)
from ent.features.office_procedures.schemas.responses import OfficeProcedureRead
from ent.features.otology.models import OfficeProcedure
from ent.features.procedures.exceptions import ProcedureRecordNotFoundError
from ent.features.procedures.mapping import blank_to_none, to_utc_naive
from ent.features.procedures.models import ProcedureRecord
from ent.features.procedures.references import ProcedureReferences
from ent.features.procedures.repository import ProcedureRecordRepository
from ent.features.recalls.dates import clinic_local_date
from ent.features.recalls.handlers import resolve_and_sync_procedure_recalls
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository

Write = OfficeProcedureCreate | OfficeProcedureUpdate
_ADAPTER: TypeAdapter[ShortProcedureWrite] = TypeAdapter(ShortProcedureWrite)
_SUPERSEDED = "office_procedure_superseded"


class OfficeProcedureService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = ProcedureReferences(session)

    async def create_procedure(
        self,
        *,
        user: CurrentUser,
        body: OfficeProcedureCreate,
        content_locale: str,
    ) -> OfficeProcedureRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        await self._assert_dates(user, body)
        concept = await self._procedure_concept(user, body.detail.subtype)
        procedure = ProcedureRecord(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(patient.id),
            ),
            procedure_concept_id=int(concept.id),
            performed_at=to_utc_naive(body.performed_at),
            performed_by_id=user.user_id,
            laterality=body.laterality.value,
            anesthesia=body.anesthesia,
            setting="office",
            indication_text=blank_to_none(body.indication_text),
            tolerance=body.tolerance,
            status="draft",
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._procedures(user).add(procedure)
        row = OfficeProcedure(
            clinic_id=user.clinic_id,
            procedure_record_id=int(procedure.id),
            subtype=body.detail.subtype,
            payload=_dump(body.detail),
            removal_due_date=removal_due_date(body.detail),
            result_due_date=result_due_date(body.detail),
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._rows(user).add(row)
        await self._replace_recalls(user, procedure, row, body, concept.code)
        return await self._present(user, row.public_id, content_locale)

    async def update_procedure(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: OfficeProcedureUpdate,
        content_locale: str,
    ) -> OfficeProcedureRead:
        self._bind(user)
        row = await self._require(user, public_id)
        procedure = row.procedure_record
        self._procedures(user).assert_draft(procedure)
        self._check_version(row, body.version)
        await self._assert_dates(user, body)
        concept = await self._procedure_concept(user, body.detail.subtype)
        procedure.encounter_id = await self._refs.encounter_id(
            user,
            body.encounter_public_id,
            patient_id=int(procedure.patient_id),
        )
        procedure.procedure_concept_id = int(concept.id)
        procedure.performed_at = to_utc_naive(body.performed_at)
        procedure.laterality = body.laterality.value
        procedure.anesthesia = body.anesthesia
        procedure.indication_text = blank_to_none(body.indication_text)
        procedure.tolerance = body.tolerance
        procedure.updated_by_id = user.user_id
        row.subtype = body.detail.subtype
        row.payload = _dump(body.detail)
        row.removal_due_date = removal_due_date(body.detail)
        row.result_due_date = result_due_date(body.detail)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._replace_recalls(user, procedure, row, body, concept.code)
        return await self._present(user, row.public_id, content_locale)

    async def get_procedure(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> OfficeProcedureRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._access(user, row, "get")
        return await self._read(user, row, content_locale)

    async def get_for_parent(
        self,
        *,
        user: CurrentUser,
        procedure_public_id: str,
        content_locale: str,
    ) -> OfficeProcedureRead:
        self._bind(user)
        procedure = await self._procedures(user).get_detail(procedure_public_id)
        if procedure is None:
            raise ProcedureRecordNotFoundError(public_id=procedure_public_id)
        await self._refs.assert_patient_visible(user, int(procedure.patient_id))
        row = await self._rows(user).get_for_procedure(procedure_public_id)
        if row is None:
            raise OfficeProcedureNotFoundError()
        self._access(user, row, "get")
        return await self._read(user, row, content_locale)

    async def list_for_patient(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
        content_locale: str,
    ) -> PageSchema[OfficeProcedureRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        listed = await self._rows(user).list_for_patient(int(patient.id), page)
        items = [await self._read(user, row, content_locale) for row in listed.items]
        self._audit.record_access(
            action="list",
            entity_type="office_procedure",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        return PageSchema(
            items=items,
            page=PageMeta(
                total=listed.total,
                limit=listed.limit,
                offset=listed.offset,
                next_cursor=None,
            ),
        )

    async def _assert_dates(self, user: CurrentUser, body: Write) -> None:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic")
        performed_on = clinic_local_date(
            to_utc_naive(body.performed_at),
            clinic.timezone,
        )
        reason = dates_before_procedure(body.detail, performed_on)
        if reason is not None:
            raise OfficeProcedureInvalidError(reason=reason)

    async def _procedure_concept(self, user: CurrentUser, subtype: str) -> Concept:
        code = PROCEDURE_BY_SUBTYPE[subtype]
        found = await TerminologyRepository(
            self._session, clinic_id=user.clinic_id
        ).list_concepts_by_codes([code])
        concept = next((row for row in found if row.code == code), None)
        if concept is None:
            raise ValidationError(reason="concept_missing", code=code)
        if concept.kind != "procedure":
            raise ValidationError(reason="procedure_concept_kind", code=code)
        return concept

    async def _replace_recalls(
        self,
        user: CurrentUser,
        procedure: ProcedureRecord,
        office: OfficeProcedure,
        body: Write,
        concept_code: str,
    ) -> None:
        del body
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic")
        performed_on = clinic_local_date(procedure.performed_at, clinic.timezone)
        await resolve_and_sync_procedure_recalls(
            self._session,
            clinic_id=user.clinic_id,
            user_id=user.user_id,
            procedure=procedure,
            procedure_concept_code=concept_code,
            performed_on=performed_on,
            office=office,
            superseded_reason=_SUPERSEDED,
            replace_existing_for_source=True,
            apply_completion_transitions=False,
        )

    async def _present(
        self,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> OfficeProcedureRead:
        await self._session.flush()
        self._session.expire_all()
        row = await self._require(user, public_id)
        return await self._read(user, row, content_locale)

    async def _read(
        self,
        user: CurrentUser,
        row: OfficeProcedure,
        content_locale: str,
    ) -> OfficeProcedureRead:
        procedure = row.procedure_record
        concept = procedure.procedure_concept
        labels = await self._refs.labels(user, {int(concept.id)}, content_locale)
        labeled = labels.get(int(concept.id))
        encounter = procedure.encounter
        return OfficeProcedureRead(
            public_id=row.public_id,
            version=int(row.version),
            procedure_id=procedure.public_id,
            procedure_status=procedure.status,
            procedure=CodeableConcept(
                concept_id=concept.public_id,
                code=concept.code,
                display=labeled[2] if labeled is not None else None,
            ),
            patient_id=procedure.patient.public_id,
            encounter_id=encounter.public_id if encounter is not None else None,
            performed_at=procedure.performed_at,
            laterality=procedure.laterality,
            anesthesia=procedure.anesthesia,
            tolerance=procedure.tolerance,
            indication_text=procedure.indication_text,
            detail=_ADAPTER.validate_python(row.payload),
            removal_due_date=row.removal_due_date,
            result_due_date=row.result_due_date,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def _require(self, user: CurrentUser, public_id: str) -> OfficeProcedure:
        row = await self._rows(user).get_detail(public_id)
        if row is None:
            raise OfficeProcedureNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(
            user, int(row.procedure_record.patient_id)
        )
        return row

    def _check_version(self, row: OfficeProcedure, version: int) -> None:
        if int(row.version) != version:
            raise OfficeProcedureVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )

    def _access(self, user: CurrentUser, row: OfficeProcedure, action: str) -> None:
        self._audit.record_access(
            action=action,
            entity_type="office_procedure",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.procedure_record.patient_id),
        )

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _rows(self, user: CurrentUser) -> ShortOfficeProcedureRepository:
        return ShortOfficeProcedureRepository(self._session, clinic_id=user.clinic_id)

    def _procedures(self, user: CurrentUser) -> ProcedureRecordRepository:
        return ProcedureRecordRepository(self._session, clinic_id=user.clinic_id)


def _dump(detail: ShortProcedureWrite) -> dict[str, object]:
    payload = detail.model_dump(mode="json", by_alias=True)
    if not isinstance(payload, dict):
        raise OfficeProcedureInvalidError(reason="payload")
    return payload
