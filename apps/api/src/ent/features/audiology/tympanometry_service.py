"""Tympanometry and acoustic reflex use cases (P4-03)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.events.bus import get_event_bus
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.audiology.tympanometry import (
    VERSION as TYMP_ENGINE_VERSION,
)
from ent.engines.audiology.tympanometry import TympanogramInput, classify_tympanogram
from ent.features.audiology.constants import TYMPANOMETRY_RESOURCE_CREATE
from ent.features.audiology.events import tympanometry_created_event
from ent.features.audiology.exceptions import (
    AudiogramVersionConflictError,
    TympanometryNotFoundError,
)
from ent.features.audiology.idempotency_util import replay_idempotent, store_idempotent
from ent.features.audiology.mapping import to_page
from ent.features.audiology.policies import (
    assert_interpret_fields,
    assert_jerger_override,
)
from ent.features.audiology.references import AudiologyReferences
from ent.features.audiology.schemas.test_requests import (
    TympanometryCreate,
    TympanometryInterpret,
    TympanometryUpdate,
)
from ent.features.audiology.schemas.test_responses import TympanometryRead
from ent.features.audiology.test_mapping import tympanometry_read
from ent.features.audiology.test_records import Tympanometry
from ent.features.audiology.test_repository import TympanometryRepository
from ent.features.encounters.repository import EncounterRepository
from ent.features.procedures.mapping import blank_to_none, to_utc_naive


class TympanometryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = AudiologyReferences(session)

    async def create_tympanogram(
        self,
        *,
        user: CurrentUser,
        body: TympanometryCreate,
        idempotency_key: str | None,
    ) -> TympanometryRead:
        self._bind(user)
        replay = await replay_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=TYMPANOMETRY_RESOURCE_CREATE,
        )
        if replay is not None:
            return await self.get_tympanogram(user=user, public_id=replay)
        assert_jerger_override(user, jerger_type=body.jerger_type_override)
        patient = await self._refs.patient(user, body.patient_public_id)
        performed_at = body.performed_at or datetime.now(UTC).replace(tzinfo=None)
        performer = body.performed_by_public_id or user.user_public_id
        row = Tympanometry(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user, body.encounter_public_id, patient_id=int(patient.id)
            ),
            performed_at=to_utc_naive(performed_at),
            performed_by_id=await self._refs.member_id(user, performer),
            ear=body.ear,
            probe_tone_hz=body.probe_tone_hz,
            ecv_ml=body.ecv_ml,
            peak_pressure_dapa=body.peak_pressure_dapa,
            compliance_ml=body.compliance_ml,
            gradient_dapa=body.gradient_dapa,
            etf_result=body.etf_result,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        if body.jerger_type_override is not None:
            _apply_engine(row, override=body.jerger_type_override, user=user)
        else:
            _apply_engine(row, override=None, user=None)
        await self._repo(user).add(row)
        await self._session.flush()
        if body.reflexes:
            await self._repo(user).sync_reflexes(
                row, body.reflexes, user_id=user.user_id
            )
        await store_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=TYMPANOMETRY_RESOURCE_CREATE,
            resource_public_id=row.public_id,
        )
        await self._session.commit()
        await get_event_bus().publish(
            tympanometry_created_event(
                clinic_id=user.clinic_id,
                tympanometry_public_id=row.public_id,
                patient_public_id=patient.public_id,
                encounter_public_id=body.encounter_public_id,
            )
        )
        return await self.get_tympanogram(user=user, public_id=row.public_id)

    async def get_tympanogram(
        self, *, user: CurrentUser, public_id: str
    ) -> TympanometryRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._audit.record_access(
            action="get",
            entity_type="tympanometry",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        loaded = await self._repo(user).get_detail(public_id)
        if loaded is None:
            raise TympanometryNotFoundError(public_id=public_id)
        return tympanometry_read(loaded)

    async def list_tympanograms(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        patient_public_id: str | None = None,
        encounter_public_id: str | None = None,
    ) -> PageSchema[TympanometryRead]:
        self._bind(user)
        patient_id, encounter_id = await self._list_filters(
            user,
            patient_public_id=patient_public_id,
            encounter_public_id=encounter_public_id,
        )
        result = await self._repo(user).list_for_patient(
            page, patient_id=patient_id, encounter_id=encounter_id
        )
        items = [tympanometry_read(row) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="tympanometry",
            clinic_id=user.clinic_id,
            patient_id=patient_id,
        )
        await self._session.commit()
        return to_page(
            items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    async def update_tympanogram(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: TympanometryUpdate,
    ) -> TympanometryRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        if body.jerger_type_override is not None:
            assert_jerger_override(user, jerger_type=body.jerger_type_override)
        if body.encounter_public_id is not None:
            row.encounter_id = await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(row.patient_id),
            )
        if body.performed_at is not None:
            row.performed_at = to_utc_naive(body.performed_at)
        if body.performed_by_public_id is not None:
            row.performed_by_id = await self._refs.member_id(
                user, body.performed_by_public_id
            )
        for field in (
            "probe_tone_hz",
            "ecv_ml",
            "peak_pressure_dapa",
            "compliance_ml",
            "gradient_dapa",
            "etf_result",
        ):
            if field in body.model_fields_set:
                setattr(row, field, getattr(body, field))
        override = body.jerger_type_override
        if any(
            field in body.model_fields_set
            for field in (
                "ecv_ml",
                "peak_pressure_dapa",
                "compliance_ml",
                "gradient_dapa",
            )
        ):
            _apply_engine(
                row,
                override=override if override is not None else None,
                user=user if override is not None else None,
                recompute_only=override is None and not row.jerger_type_is_overridden,
            )
        elif override is not None:
            _apply_engine(row, override=override, user=user)
        if body.reflexes is not None:
            await self._repo(user).sync_reflexes(
                row, body.reflexes, user_id=user.user_id
            )
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_tympanogram(user=user, public_id=row.public_id)

    async def interpret_tympanogram(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: TympanometryInterpret,
    ) -> TympanometryRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        assert_interpret_fields(
            user,
            interpretation_text=body.interpretation_text,
            is_baseline=None,
        )
        if body.jerger_type is not None:
            assert_jerger_override(user, jerger_type=body.jerger_type)
            now = datetime.now(UTC).replace(tzinfo=None)
            row.jerger_type = body.jerger_type
            row.jerger_type_is_overridden = True
            row.overridden_by_id = user.user_id
            row.overridden_at = now
        if body.interpretation_text is not None:
            row.interpretation_text = blank_to_none(body.interpretation_text)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_tympanogram(user=user, public_id=row.public_id)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _repo(self, user: CurrentUser) -> TympanometryRepository:
        return TympanometryRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> Tympanometry:
        row = await self._repo(user).get_detail(public_id)
        if row is None:
            raise TympanometryNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    def _check_version(self, row: Tympanometry, version: int) -> None:
        if int(row.version) != version:
            raise AudiogramVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )

    async def _list_filters(
        self,
        user: CurrentUser,
        *,
        patient_public_id: str | None,
        encounter_public_id: str | None,
    ) -> tuple[int | None, int | None]:
        patient_id = None
        encounter_id = None
        if patient_public_id is not None:
            patient_id = int((await self._refs.patient(user, patient_public_id)).id)
        if encounter_public_id is not None:
            encounter = await EncounterRepository(
                self._session, clinic_id=user.clinic_id
            ).get_by_public_id(encounter_public_id)
            if encounter is None:
                raise ValidationError(reason="encounter_not_found")
            encounter_id = int(encounter.id)
            if patient_id is None:
                patient_id = int(encounter.patient_id)
            elif patient_id != int(encounter.patient_id):
                raise ValidationError(reason="encounter_patient")
        return patient_id, encounter_id


def _apply_engine(
    row: Tympanometry,
    *,
    override: str | None,
    user: CurrentUser | None,
    recompute_only: bool = True,
) -> None:
    result = classify_tympanogram(
        TympanogramInput(
            ecv_ml=row.ecv_ml,
            peak_pressure_dapa=row.peak_pressure_dapa,
            compliance_ml=row.compliance_ml,
            gradient_dapa=row.gradient_dapa,
        )
    )
    row.suggested_jerger_type = result.suggested_jerger_type
    row.large_canal_volume_flag = result.large_canal_volume_flag
    row.engine_version = TYMP_ENGINE_VERSION
    if override is not None and user is not None:
        now = datetime.now(UTC).replace(tzinfo=None)
        row.jerger_type = override
        row.jerger_type_is_overridden = True
        row.overridden_by_id = user.user_id
        row.overridden_at = now
    elif recompute_only and not row.jerger_type_is_overridden:
        row.jerger_type = result.suggested_jerger_type
