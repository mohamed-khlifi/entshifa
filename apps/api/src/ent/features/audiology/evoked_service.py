"""OAE and ABR use cases (P4-03)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.audiology.abr import VERSION as ABR_ENGINE_VERSION
from ent.engines.audiology.abr import AbrWaveInput, compute_abr_metrics
from ent.features.audiology.calc_settings import resolve_abr_interaural_threshold_ms
from ent.features.audiology.constants import ABR_RESOURCE_CREATE, OAE_RESOURCE_CREATE
from ent.features.audiology.exceptions import (
    AbrResultNotFoundError,
    AudiogramVersionConflictError,
    OaeResultNotFoundError,
)
from ent.features.audiology.idempotency_util import replay_idempotent, store_idempotent
from ent.features.audiology.mapping import to_page
from ent.features.audiology.policies import assert_interpret_fields
from ent.features.audiology.references import AudiologyReferences
from ent.features.audiology.schemas.test_requests import (
    AbrInterpret,
    AbrResultCreate,
    AbrResultUpdate,
    OaeInterpret,
    OaeResultCreate,
    OaeResultUpdate,
)
from ent.features.audiology.schemas.test_responses import AbrResultRead, OaeResultRead
from ent.features.audiology.test_mapping import abr_read, oae_read
from ent.features.audiology.test_records import AbrResult, OaeResult
from ent.features.audiology.test_repository import (
    AbrResultRepository,
    OaeResultRepository,
)
from ent.features.encounters.repository import EncounterRepository
from ent.features.procedures.mapping import blank_to_none, to_utc_naive


class OaeResultService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = AudiologyReferences(session)

    async def create_oae_result(
        self,
        *,
        user: CurrentUser,
        body: OaeResultCreate,
        idempotency_key: str | None,
    ) -> OaeResultRead:
        self._bind(user)
        replay = await replay_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=OAE_RESOURCE_CREATE,
        )
        if replay is not None:
            return await self.get_oae_result(user=user, public_id=replay)
        patient = await self._refs.patient(user, body.patient_public_id)
        performed_at = body.performed_at or datetime.now(UTC).replace(tzinfo=None)
        performer = body.performed_by_public_id or user.user_public_id
        row = OaeResult(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user, body.encounter_public_id, patient_id=int(patient.id)
            ),
            performed_at=to_utc_naive(performed_at),
            performed_by_id=await self._refs.member_id(user, performer),
            ear=body.ear,
            oae_type=body.oae_type,
            overall_result=body.overall_result,
            screening_stage=body.screening_stage,
            bands=[item.model_dump(mode="json") for item in body.bands],
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._repo(user).add(row)
        await store_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=OAE_RESOURCE_CREATE,
            resource_public_id=row.public_id,
        )
        await self._session.commit()
        return await self.get_oae_result(user=user, public_id=row.public_id)

    async def get_oae_result(
        self, *, user: CurrentUser, public_id: str
    ) -> OaeResultRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._audit.record_access(
            action="get",
            entity_type="oae_result",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        loaded = await self._repo(user).get_detail(public_id)
        if loaded is None:
            raise OaeResultNotFoundError(public_id=public_id)
        return oae_read(loaded)

    async def list_oae_results(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        patient_public_id: str | None = None,
        encounter_public_id: str | None = None,
    ) -> PageSchema[OaeResultRead]:
        self._bind(user)
        patient_id, encounter_id = await _list_filters(
            self._session, self._refs, user, patient_public_id, encounter_public_id
        )
        result = await self._repo(user).list_for_patient(
            page, patient_id=patient_id, encounter_id=encounter_id
        )
        items = [oae_read(row) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="oae_result",
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

    async def update_oae_result(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: OaeResultUpdate,
    ) -> OaeResultRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
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
        for field in ("oae_type", "overall_result", "screening_stage"):
            if field in body.model_fields_set:
                setattr(row, field, getattr(body, field))
        if body.bands is not None:
            row.bands = [item.model_dump(mode="json") for item in body.bands]
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_oae_result(user=user, public_id=row.public_id)

    async def interpret_oae_result(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: OaeInterpret,
    ) -> OaeResultRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        assert_interpret_fields(
            user, interpretation_text=body.interpretation_text, is_baseline=None
        )
        if body.interpretation_text is not None:
            row.interpretation_text = blank_to_none(body.interpretation_text)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_oae_result(user=user, public_id=row.public_id)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _repo(self, user: CurrentUser) -> OaeResultRepository:
        return OaeResultRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> OaeResult:
        row = await self._repo(user).get_detail(public_id)
        if row is None:
            raise OaeResultNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    def _check_version(self, row: OaeResult, version: int) -> None:
        if int(row.version) != version:
            raise AudiogramVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )


class AbrResultService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = AudiologyReferences(session)

    async def create_abr_result(
        self,
        *,
        user: CurrentUser,
        body: AbrResultCreate,
        idempotency_key: str | None,
    ) -> AbrResultRead:
        self._bind(user)
        replay = await replay_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=ABR_RESOURCE_CREATE,
        )
        if replay is not None:
            return await self.get_abr_result(user=user, public_id=replay)
        patient = await self._refs.patient(user, body.patient_public_id)
        performed_at = body.performed_at or datetime.now(UTC).replace(tzinfo=None)
        performer = body.performed_by_public_id or user.user_public_id
        row = AbrResult(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user, body.encounter_public_id, patient_id=int(patient.id)
            ),
            performed_at=to_utc_naive(performed_at),
            performed_by_id=await self._refs.member_id(user, performer),
            ear=body.ear,
            stimulus=body.stimulus,
            stimulus_frequency_hz=body.stimulus_frequency_hz,
            threshold_db=body.threshold_db,
            intensity_db=body.intensity_db,
            wave_i_ms=body.wave_i_ms,
            wave_iii_ms=body.wave_iii_ms,
            wave_v_ms=body.wave_v_ms,
            assr_thresholds=(
                [item.model_dump(mode="json") for item in body.assr_thresholds]
                if body.assr_thresholds
                else None
            ),
            morphology=body.morphology,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await _apply_abr_engine(self._session, user, row, body.contralateral_wave_v_ms)
        await self._repo(user).add(row)
        await store_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=ABR_RESOURCE_CREATE,
            resource_public_id=row.public_id,
        )
        await self._session.commit()
        return await self.get_abr_result(user=user, public_id=row.public_id)

    async def get_abr_result(
        self, *, user: CurrentUser, public_id: str
    ) -> AbrResultRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._audit.record_access(
            action="get",
            entity_type="abr_result",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        loaded = await self._repo(user).get_detail(public_id)
        if loaded is None:
            raise AbrResultNotFoundError(public_id=public_id)
        return abr_read(loaded)

    async def list_abr_results(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        patient_public_id: str | None = None,
        encounter_public_id: str | None = None,
    ) -> PageSchema[AbrResultRead]:
        self._bind(user)
        patient_id, encounter_id = await _list_filters(
            self._session, self._refs, user, patient_public_id, encounter_public_id
        )
        result = await self._repo(user).list_for_patient(
            page, patient_id=patient_id, encounter_id=encounter_id
        )
        items = [abr_read(row) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="abr_result",
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

    async def update_abr_result(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AbrResultUpdate,
    ) -> AbrResultRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
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
            "stimulus",
            "stimulus_frequency_hz",
            "threshold_db",
            "intensity_db",
            "wave_i_ms",
            "wave_iii_ms",
            "wave_v_ms",
            "morphology",
        ):
            if field in body.model_fields_set:
                setattr(row, field, getattr(body, field))
        if body.assr_thresholds is not None:
            row.assr_thresholds = [
                item.model_dump(mode="json") for item in body.assr_thresholds
            ]
        await _apply_abr_engine(self._session, user, row, body.contralateral_wave_v_ms)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_abr_result(user=user, public_id=row.public_id)

    async def interpret_abr_result(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AbrInterpret,
    ) -> AbrResultRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        assert_interpret_fields(
            user, interpretation_text=body.interpretation_text, is_baseline=None
        )
        if body.interpretation_text is not None:
            row.interpretation_text = blank_to_none(body.interpretation_text)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        return await self.get_abr_result(user=user, public_id=row.public_id)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _repo(self, user: CurrentUser) -> AbrResultRepository:
        return AbrResultRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> AbrResult:
        row = await self._repo(user).get_detail(public_id)
        if row is None:
            raise AbrResultNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    def _check_version(self, row: AbrResult, version: int) -> None:
        if int(row.version) != version:
            raise AudiogramVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )


async def _list_filters(
    session: AsyncSession,
    refs: AudiologyReferences,
    user: CurrentUser,
    patient_public_id: str | None,
    encounter_public_id: str | None,
) -> tuple[int | None, int | None]:
    patient_id = None
    encounter_id = None
    if patient_public_id is not None:
        patient_id = int((await refs.patient(user, patient_public_id)).id)
    if encounter_public_id is not None:
        encounter = await EncounterRepository(
            session, clinic_id=user.clinic_id
        ).get_by_public_id(encounter_public_id)
        if encounter is None:
            raise ValidationError(reason="encounter_not_found")
        encounter_id = int(encounter.id)
        if patient_id is None:
            patient_id = int(encounter.patient_id)
        elif patient_id != int(encounter.patient_id):
            raise ValidationError(reason="encounter_patient")
    return patient_id, encounter_id


async def _apply_abr_engine(
    session: AsyncSession,
    user: CurrentUser,
    row: AbrResult,
    contralateral_wave_v_ms: Decimal | None,
) -> None:
    contra = contralateral_wave_v_ms
    if contra is None and row.wave_v_ms is not None:
        other = await AbrResultRepository(
            session, clinic_id=user.clinic_id
        ).find_contralateral_wave_v(
            patient_id=int(row.patient_id),
            ear=row.ear,
            performed_at=row.performed_at,
            exclude_id=int(row.id) if row.id is not None else None,
        )
        if other is not None and other.wave_v_ms is not None:
            contra = other.wave_v_ms
    threshold = await resolve_abr_interaural_threshold_ms(session, user)
    metrics = compute_abr_metrics(
        AbrWaveInput(
            wave_i_ms=row.wave_i_ms,
            wave_iii_ms=row.wave_iii_ms,
            wave_v_ms=row.wave_v_ms,
        ),
        contralateral_wave_v_ms=contra,
        threshold_ms=threshold,
    )
    row.i_iii_ms = metrics.i_iii_ms
    row.iii_v_ms = metrics.iii_v_ms
    row.i_v_ms = metrics.i_v_ms
    row.interaural_v_diff_ms = metrics.interaural_v_diff_ms
    row.interaural_v_flag = metrics.interaural_v_flag
    row.engine_version = ABR_ENGINE_VERSION
