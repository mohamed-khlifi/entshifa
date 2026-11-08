"""Calculator registry use cases (P5-05)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.engines.calculator_catalog import (
    evaluate_calculator,
    get_calculator_spec,
    registered_calculators,
)
from ent.engines.calculator_errors import CalculatorInputError
from ent.features.calculators.exceptions import (
    CalculatorInvalidInputError,
    CalculatorNotFoundError,
    CalculatorNotInteractiveError,
)
from ent.features.calculators.mapping import to_result_read, to_saved_read, to_spec_read
from ent.features.calculators.schemas.requests import CalculatorEvaluateRequest
from ent.features.calculators.schemas.responses import (
    CalculationResultRead,
    CalculatorSpecRead,
    SavedCalculationResultRead,
)
from ent.features.encounters.constants import LOCKED_STATUSES
from ent.features.encounters.exceptions import EncounterLockedError
from ent.features.encounters.models import Encounter
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import Patient
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.features.prescriptions.repository import CalculationResultRepository
from ent.features.prescriptions.service import _calculation_row


class CalculatorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def list_calculators(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        domain: str | None,
        interactive_only: bool,
    ) -> PageSchema[CalculatorSpecRead]:
        self._bind(user)
        specs = [
            spec
            for spec in registered_calculators()
            if (domain is None or spec.domain == domain)
            and (not interactive_only or spec.interactive)
        ]
        total = len(specs)
        offset = page.offset or 0
        items = [to_spec_read(spec) for spec in specs[offset : offset + page.limit]]
        self._audit.record_access(
            action="list",
            entity_type="calculator",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return PageSchema(
            items=items,
            page=PageMeta(
                total=total,
                limit=page.limit,
                offset=page.offset,
                next_cursor=None,
            ),
        )

    async def get_calculator(
        self, *, user: CurrentUser, code: str
    ) -> CalculatorSpecRead:
        self._bind(user)
        spec = get_calculator_spec(code)
        if spec is None:
            raise CalculatorNotFoundError(code=code)
        self._audit.record_access(
            action="get",
            entity_type="calculator",
            clinic_id=user.clinic_id,
            entity_public_id=code,
        )
        await self._session.commit()
        return to_spec_read(spec)

    async def evaluate(
        self,
        *,
        user: CurrentUser,
        code: str,
        body: CalculatorEvaluateRequest,
    ) -> CalculationResultRead:
        self._bind(user)
        spec = get_calculator_spec(code)
        if spec is None:
            raise CalculatorNotFoundError(code=code)
        if not spec.interactive:
            raise CalculatorNotInteractiveError(code=code)
        try:
            result = evaluate_calculator(code, body.inputs)
        except CalculatorInputError as exc:
            field = exc.context.get("field")
            raise CalculatorInvalidInputError(reason=exc.code, field=field) from exc
        saved_id: str | None = None
        computed_at: datetime | None = None
        should_save = body.save_to_consultation or body.patient_id is not None
        if should_save:
            patient, encounter = await self._resolve_save_targets(user, body)
            if encounter is not None and encounter.status in LOCKED_STATUSES:
                raise EncounterLockedError(
                    public_id=encounter.public_id,
                    status=encounter.status,
                )
            now = datetime.now(UTC)
            row = _calculation_row(user, patient, encounter, result, now)
            await CalculationResultRepository(
                self._session, clinic_id=user.clinic_id
            ).add(row)
            await self._session.flush()
            saved_id = row.public_id
            computed_at = row.computed_at
            self._audit.record_write(
                action="save",
                entity=row,
                clinic_id=user.clinic_id,
                after={"calculatorCode": code, "value": result.value},
            )
        else:
            self._audit.record_access(
                action="evaluate",
                entity_type="calculator",
                clinic_id=user.clinic_id,
                entity_public_id=code,
            )
        await self._session.commit()
        return to_result_read(
            result,
            saved_result_id=saved_id,
            computed_at=computed_at,
        )

    async def list_patient_calculations(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
        calculator_code: str | None,
        encounter_public_id: str | None,
    ) -> PageSchema[SavedCalculationResultRead]:
        self._bind(user)
        patient = await self._require_patient(user, patient_public_id)
        encounter_id: int | None = None
        encounter_public: str | None = None
        if encounter_public_id is not None:
            encounter = await self._require_encounter(user, encounter_public_id)
            if int(encounter.patient_id) != int(patient.id):
                raise NotFoundError(resource="encounter", publicId=encounter_public_id)
            encounter_id = int(encounter.id)
            encounter_public = encounter.public_id
        rows = await CalculationResultRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(
            patient_id=int(patient.id),
            page=page,
            calculator_code=calculator_code,
            encounter_id=encounter_id,
        )
        items = [
            to_saved_read(
                row,
                patient_public_id=patient.public_id,
                encounter_public_id=encounter_public,
            )
            for row in rows.items
        ]
        self._audit.record_access(
            action="list",
            entity_type="calculation_result",
            clinic_id=user.clinic_id,
            entity_id=int(patient.id),
            entity_public_id=patient.public_id,
        )
        await self._session.commit()
        return PageSchema(
            items=items,
            page=PageMeta(
                total=rows.total,
                limit=rows.limit,
                offset=rows.offset,
                next_cursor=None,
            ),
        )

    async def _resolve_save_targets(
        self,
        user: CurrentUser,
        body: CalculatorEvaluateRequest,
    ) -> tuple[Patient, Encounter | None]:
        if body.patient_id is None:
            raise CalculatorInvalidInputError(reason="patient_required")
        patient = await self._require_patient(user, body.patient_id)
        encounter: Encounter | None = None
        if body.encounter_id is not None:
            encounter = await self._require_encounter(user, body.encounter_id)
            if int(encounter.patient_id) != int(patient.id):
                raise CalculatorInvalidInputError(
                    reason="encounter_patient",
                    field="encounter_id",
                )
        return patient, encounter

    async def _require_patient(self, user: CurrentUser, public_id: str) -> Patient:
        row = await PatientRepository(
            self._session, clinic_id=user.clinic_id
        ).get_visible(public_id, created_by_id=created_by_scope(user))
        if row is None:
            raise NotFoundError(resource="patient", publicId=public_id)
        return row

    async def _require_encounter(self, user: CurrentUser, public_id: str) -> Encounter:
        row = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None:
            raise NotFoundError(resource="encounter", publicId=public_id)
        return row

    def _bind(self, user: CurrentUser) -> None:
        set_user_id(user.user_id)
        set_clinic_id(user.clinic_id)
