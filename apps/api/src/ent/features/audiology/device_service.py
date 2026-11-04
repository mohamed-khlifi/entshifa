"""Hearing devices, candidacy and OME use cases (P4-06)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.audiology.candidacy import (
    REFERENCE as CANDIDACY_REFERENCE,
)
from ent.engines.audiology.candidacy import VERSION as CANDIDACY_VERSION
from ent.engines.audiology.candidacy import CandidacyInput, evaluate_device_candidacy
from ent.engines.audiology.ehdi_136 import VERSION as EHDI_VERSION
from ent.engines.audiology.ehdi_136 import Ehdi136Input, evaluate_ehdi_136
from ent.features.audiology.constants import HEARING_DEVICE_RESOURCE_CREATE
from ent.features.audiology.device_mapping import (
    candidacy_evaluation_read,
    hearing_device_read,
    ome_episode_read,
    pediatric_read,
)
from ent.features.audiology.device_models import (
    HearingDevice,
    OmeEpisode,
    PediatricAudiologyRecord,
)
from ent.features.audiology.device_repository import (
    HearingDeviceRepository,
    OmeEpisodeRepository,
    PediatricAudiologyRepository,
)
from ent.features.audiology.exceptions import (
    HearingDeviceNotFoundError,
    HearingDeviceVersionConflictError,
    OmeEpisodeNotFoundError,
    OmeEpisodeVersionConflictError,
)
from ent.features.audiology.idempotency_util import replay_idempotent, store_idempotent
from ent.features.audiology.mapping import to_page
from ent.features.audiology.models import Audiogram
from ent.features.audiology.policies import assert_can_interpret
from ent.features.audiology.references import AudiologyReferences
from ent.features.audiology.repository import AudiogramRepository
from ent.features.audiology.schemas.device_requests import (
    CandidacyConfirm,
    CandidacyEvaluate,
    HearingDeviceCreate,
    HearingDeviceUpdate,
    MilestonesUpdate,
    NewbornScreeningUpdate,
    OmeEpisodeCreate,
    OmeEpisodeUpdate,
)
from ent.features.audiology.schemas.device_responses import (
    CandidacyConfirmationRead,
    CandidacyEvaluationRead,
    HearingDeviceRead,
    OmeEpisodeRead,
    PediatricAudiologyRead,
    PediatricSummaryRead,
)
from ent.features.audiology.test_repository import SpeechAudiometryRepository
from ent.features.clinics.repository import ClinicRepository
from ent.features.patients.models import Patient, PatientFlag
from ent.features.patients.repository import PatientFlagRepository
from ent.features.procedures.mapping import blank_to_none
from ent.features.recalls.dates import clinic_local_date
from ent.features.recalls.handlers import (
    cancel_open_recalls_for_reason,
    materialize_protocol_rule_recall,
)


class HearingDeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = AudiologyReferences(session)

    async def create_device(
        self,
        *,
        user: CurrentUser,
        body: HearingDeviceCreate,
        idempotency_key: str | None,
    ) -> HearingDeviceRead:
        self._bind(user)
        replay = await replay_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=HEARING_DEVICE_RESOURCE_CREATE,
        )
        if replay is not None:
            row = await self._devices(user).get_detail(replay)
            if row is None:
                raise HearingDeviceNotFoundError(public_id=replay)
            return hearing_device_read(row)
        patient = await self._refs.patient(user, body.patient_public_id)
        row = HearingDevice(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            ear=body.ear,
            device_type=body.device_type,
            brand=blank_to_none(body.brand),
            model=blank_to_none(body.model),
            serial=blank_to_none(body.serial),
            fitted_on=body.fitted_on,
            fitted_by=blank_to_none(body.fitted_by),
            warranty_end=body.warranty_end,
            last_programmed_on=body.last_programmed_on,
            battery_type=blank_to_none(body.battery_type),
            daily_use_hours=body.daily_use_hours,
            satisfaction=body.satisfaction,
            status=body.status,
            aided_thresholds=_aided_json(body.aided_thresholds),
            surgeon=blank_to_none(body.surgeon),
            surgery_date=body.surgery_date,
            electrode_array=blank_to_none(body.electrode_array),
            implant_activation_date=body.implant_activation_date,
            mapping_dates=_dates_json(body.mapping_dates),
            complications=blank_to_none(body.complications),
            mri_conditions=blank_to_none(body.mri_conditions),
            notes=blank_to_none(body.notes),
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._devices(user).add(row)
        await self._session.flush()
        await self._sync_device_recalls(user, row)
        await self._sync_cochlear_implant_flag(user, int(patient.id), row)
        await store_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=HEARING_DEVICE_RESOURCE_CREATE,
            resource_public_id=row.public_id,
        )
        await self._session.commit()
        loaded = await self._devices(user).get_detail(row.public_id)
        assert loaded is not None
        return hearing_device_read(loaded)

    async def list_devices(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams,
    ) -> PageSchema[HearingDeviceRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        result = await self._devices(user).list_for_patient(int(patient.id), page)
        items = [hearing_device_read(row) for row in result.items]
        await self._session.commit()
        return to_page(
            items, total=result.total, limit=result.limit, offset=result.offset
        )

    async def update_device(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: HearingDeviceUpdate,
    ) -> HearingDeviceRead:
        self._bind(user)
        row = await self._require_device(user, public_id)
        if int(row.version) != body.version:
            raise HearingDeviceVersionConflictError(
                server_version=int(row.version),
                client_version=body.version,
            )
        data = body.model_dump(exclude_unset=True)
        for field in (
            "brand",
            "model",
            "serial",
            "fitted_by",
            "battery_type",
            "complications",
            "mri_conditions",
            "notes",
            "surgeon",
            "electrode_array",
        ):
            if field in data:
                setattr(row, field, blank_to_none(data[field]))
        for field in (
            "fitted_on",
            "warranty_end",
            "last_programmed_on",
            "surgery_date",
            "implant_activation_date",
            "daily_use_hours",
            "satisfaction",
            "status",
        ):
            if field in data:
                setattr(row, field, data[field])
        if "aided_thresholds" in data:
            row.aided_thresholds = _aided_json(body.aided_thresholds)
        if "mapping_dates" in data:
            row.mapping_dates = _dates_json(body.mapping_dates)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._sync_device_recalls(user, row)
        await self._sync_cochlear_implant_flag(user, int(row.patient_id), row)
        await self._session.commit()
        loaded = await self._devices(user).get_detail(row.public_id)
        assert loaded is not None
        return hearing_device_read(loaded)

    async def evaluate_candidacy(
        self,
        *,
        user: CurrentUser,
        body: CandidacyEvaluate,
    ) -> CandidacyEvaluationRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        audiogram = await self._resolve_audiogram(
            user, patient, body.audiogram_public_id
        )
        speech = await self._latest_speech(user, int(patient.id))
        result = evaluate_device_candidacy(
            CandidacyInput(
                pta_right=audiogram.pta_right if audiogram else None,
                pta_left=audiogram.pta_left if audiogram else None,
                wrs_right_percent=speech.get("right"),
                wrs_left_percent=speech.get("left"),
                loss_type_right=audiogram.loss_type_right if audiogram else None,
                loss_type_left=audiogram.loss_type_left if audiogram else None,
                hearing_aid_trial_completed=body.hearing_aid_trial_completed,
                imaging_clearance=body.imaging_clearance,
                communication_impact_assessed=body.communication_impact_assessed,
            )
        )
        await self._session.commit()
        return candidacy_evaluation_read(
            result,
            engine_version=CANDIDACY_VERSION,
            engine_reference=CANDIDACY_REFERENCE,
        )

    async def confirm_candidacy(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: CandidacyConfirm,
    ) -> CandidacyConfirmationRead:
        self._bind(user)
        assert_can_interpret(user)
        patient = await self._refs.patient(user, patient_public_id)
        evaluation = await self.evaluate_candidacy(
            user=user,
            body=CandidacyEvaluate(
                patient_public_id=patient_public_id,
                audiogram_public_id=body.audiogram_public_id,
                hearing_aid_trial_completed=body.hearing_aid_trial_completed,
                imaging_clearance=body.imaging_clearance,
                communication_impact_assessed=body.communication_impact_assessed,
            ),
        )
        repo = PediatricAudiologyRepository(self._session, clinic_id=user.clinic_id)
        record = await repo.get_for_patient(int(patient.id))
        now = datetime.now(UTC).replace(tzinfo=None)
        snapshot = evaluation.model_dump(mode="json")
        if record is None:
            record = PediatricAudiologyRecord(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                patient_id=int(patient.id),
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            await repo.add(record)
        record.candidacy_snapshot = snapshot
        if body.kind == "hearing_aid":
            record.ha_candidacy_confirmed_at = now
            record.ha_candidacy_confirmed_by_id = user.user_id
            record.ha_candidacy_confirmed_kind = body.kind
        else:
            record.ci_candidacy_confirmed_at = now
            record.ci_candidacy_confirmed_by_id = user.user_id
            record.ci_candidacy_confirmed_kind = body.kind
        record.updated_by_id = user.user_id
        record.version = int(record.version) + 1
        await self._session.commit()
        return CandidacyConfirmationRead(
            kind=body.kind,
            confirmed_at=now,
            confirmed_by_public_id=user.user_public_id,
            evaluation=evaluation,
        )

    async def get_pediatric_summary(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        ome_page: PaginationParams,
    ) -> PediatricSummaryRead:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        pediatric = await PediatricAudiologyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_for_patient(int(patient.id))
        ome = await OmeEpisodeRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(int(patient.id), ome_page)
        await self._session.commit()
        return PediatricSummaryRead(
            pediatric=pediatric_read(pediatric) if pediatric else None,
            ome_episodes=[ome_episode_read(row) for row in ome.items],
        )

    async def update_newborn_screening(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: NewbornScreeningUpdate,
    ) -> PediatricAudiologyRead:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        if patient.birth_date is None:
            raise ValidationError(reason="patient_birth_date_required")
        record = await self._pediatric_record(user, int(patient.id))
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(record, key, value)
        await self._recompute_ehdi(user, patient, record)
        record.updated_by_id = user.user_id
        record.version = int(record.version) + 1
        await self._session.commit()
        loaded = await PediatricAudiologyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_for_patient(int(patient.id))
        assert loaded is not None
        return pediatric_read(loaded)

    async def update_milestones(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: MilestonesUpdate,
    ) -> PediatricAudiologyRead:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        record = await self._pediatric_record(user, int(patient.id))
        record.speech_language_milestones = dict(body.milestones)
        record.updated_by_id = user.user_id
        record.version = int(record.version) + 1
        await self._session.commit()
        loaded = await PediatricAudiologyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_for_patient(int(patient.id))
        assert loaded is not None
        return pediatric_read(loaded)

    async def create_ome_episode(
        self,
        *,
        user: CurrentUser,
        body: OmeEpisodeCreate,
        idempotency_key: str | None,
    ) -> OmeEpisodeRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        start_on = body.watchful_waiting_start_on or body.first_seen_on
        due_on = start_on + timedelta(days=90)
        row = OmeEpisode(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(patient.id),
            ),
            audiogram_id=await self._audiogram_id(user, body.audiogram_public_id),
            tympanometry_id=await self._tympanometry_id(
                user, body.tympanometry_public_id
            ),
            laterality=body.laterality,
            first_seen_on=body.first_seen_on,
            hearing_level_db=body.hearing_level_db,
            watchful_waiting_start_on=start_on,
            watchful_waiting_due_on=due_on,
            status="watchful_waiting",
            notes=blank_to_none(body.notes),
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await OmeEpisodeRepository(self._session, clinic_id=user.clinic_id).add(row)
        await self._session.flush()
        await materialize_protocol_rule_recall(
            self._session,
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            user_id=user.user_id,
            protocol_code="PROT.OME_WATCHFUL_WAITING",
            rule_sequence=1,
            anchor_date=start_on,
            laterality=body.laterality,
            source_type="manual",
            source_id=int(row.id),
        )
        await self._session.commit()
        loaded = await OmeEpisodeRepository(
            self._session, clinic_id=user.clinic_id
        ).get_detail(row.public_id)
        assert loaded is not None
        return ome_episode_read(loaded)

    async def update_ome_episode(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: OmeEpisodeUpdate,
    ) -> OmeEpisodeRead:
        self._bind(user)
        repo = OmeEpisodeRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_detail(public_id)
        if row is None:
            raise OmeEpisodeNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        if int(row.version) != body.version:
            raise OmeEpisodeVersionConflictError(
                server_version=int(row.version),
                client_version=body.version,
            )
        if body.hearing_level_db is not None:
            row.hearing_level_db = body.hearing_level_db
        if body.notes is not None:
            row.notes = blank_to_none(body.notes)
        if body.status is not None:
            row.status = body.status
        if body.resolved_on is not None:
            row.resolved_on = body.resolved_on
        if body.status in ("resolved", "tubes_inserted"):
            await cancel_open_recalls_for_reason(
                self._session,
                clinic_id=user.clinic_id,
                patient_id=int(row.patient_id),
                reason_key="audiology_ome_watchful_waiting",
                cancelled_reason="ome_resolved",
                user_id=user.user_id,
            )
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.commit()
        loaded = await repo.get_detail(public_id)
        assert loaded is not None
        return ome_episode_read(loaded)

    async def _pediatric_record(
        self, user: CurrentUser, patient_id: int
    ) -> PediatricAudiologyRecord:
        repo = PediatricAudiologyRepository(self._session, clinic_id=user.clinic_id)
        record = await repo.get_for_patient(patient_id)
        if record is None:
            record = PediatricAudiologyRecord(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                patient_id=patient_id,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            await repo.add(record)
            await self._session.flush()
        return record

    async def _recompute_ehdi(
        self,
        user: CurrentUser,
        patient: Patient,
        record: PediatricAudiologyRecord,
    ) -> None:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        today = clinic_local_date(
            datetime.now(UTC), clinic.timezone if clinic else "UTC"
        )
        assert patient.birth_date is not None
        screen_refer = (
            _is_refer(record.screen_result_right)
            or _is_refer(record.screen_result_left)
            or _is_refer(record.rescreen_result_right)
            or _is_refer(record.rescreen_result_left)
        )
        result = evaluate_ehdi_136(
            Ehdi136Input(
                birth_date=patient.birth_date,
                as_of_date=today,
                screen_date=record.screen_date,
                screen_refer=screen_refer,
                rescreen_date=record.rescreen_date,
                diagnostic_abr_date=record.diagnostic_abr_date,
                permanent_hearing_loss=bool(record.permanent_hearing_loss),
                intervention_date=record.intervention_date,
            )
        )
        record.screen_by_1m_status = result.screen_by_1m.value
        record.diagnosis_by_3m_status = result.diagnosis_by_3m.value
        record.intervention_by_6m_status = result.intervention_by_6m.value
        record.ehdi_engine_version = EHDI_VERSION

    async def _sync_device_recalls(self, user: CurrentUser, row: HearingDevice) -> None:
        if row.status not in ("active", "trial"):
            return
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        anchor = row.fitted_on or clinic_local_date(
            datetime.now(UTC), clinic.timezone if clinic else "UTC"
        )
        attrs: dict[str, Any] = {}
        if row.warranty_end is not None:
            attrs["warranty_end"] = row.warranty_end
        await materialize_protocol_rule_recall(
            self._session,
            clinic_id=user.clinic_id,
            patient_id=int(row.patient_id),
            user_id=user.user_id,
            protocol_code="PROT.HEARING_DEVICE_FOLLOWUP",
            rule_sequence=1,
            anchor_date=anchor,
            laterality=row.ear,
            attributes=attrs,
            source_type="manual",
            source_id=int(row.id),
        )
        if row.warranty_end is not None:
            await materialize_protocol_rule_recall(
                self._session,
                clinic_id=user.clinic_id,
                patient_id=int(row.patient_id),
                user_id=user.user_id,
                protocol_code="PROT.HEARING_DEVICE_FOLLOWUP",
                rule_sequence=2,
                anchor_date=anchor,
                laterality=row.ear,
                attributes=attrs,
                source_type="manual",
                source_id=int(row.id),
            )

    async def _sync_cochlear_implant_flag(
        self,
        user: CurrentUser,
        patient_id: int,
        device: HearingDevice,
    ) -> None:
        flag_repo = PatientFlagRepository(self._session, clinic_id=user.clinic_id)
        active_flags = await flag_repo.list_active(
            flag_code="cochlear_implant", patient_id=patient_id, limit=20
        )
        should_have = device.device_type == "cochlear_implant" and device.status in (
            "active",
            "trial",
        )
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        today = clinic_local_date(
            datetime.now(UTC), clinic.timezone if clinic else "UTC"
        )
        if should_have:
            if not active_flags:
                await flag_repo.add(
                    PatientFlag(
                        public_id=new_ulid(),
                        clinic_id=user.clinic_id,
                        patient_id=patient_id,
                        flag_code="cochlear_implant",
                        laterality=device.ear,
                        started_on=today,
                        is_auto=True,
                        created_by_id=user.user_id,
                        updated_by_id=user.user_id,
                    )
                )
            return
        for flag in active_flags:
            if flag.is_auto:
                flag.ended_on = today
                flag.updated_by_id = user.user_id
                flag.version = int(flag.version) + 1

    async def _resolve_audiogram(
        self,
        user: CurrentUser,
        patient: Patient,
        audiogram_public_id: str | None,
    ) -> Audiogram | None:
        repo = AudiogramRepository(self._session, clinic_id=user.clinic_id)
        if audiogram_public_id:
            row = await repo.get_detail(audiogram_public_id)
            if row is None or int(row.patient_id) != int(patient.id):
                raise ValidationError(reason="audiogram_not_found")
            return row
        page = await repo.list_audiograms(
            PaginationParams(limit=1, offset=0),
            patient_id=int(patient.id),
        )
        return page.items[0] if page.items else None

    async def _latest_speech(
        self, user: CurrentUser, patient_id: int
    ) -> dict[str, int | None]:
        repo = SpeechAudiometryRepository(self._session, clinic_id=user.clinic_id)
        page = await repo.list_for_patient(
            PaginationParams(limit=20, offset=0),
            patient_id=patient_id,
        )
        by_ear: dict[str, int | None] = {"right": None, "left": None}
        for row in page.items:
            if by_ear.get(row.ear) is None and row.wrs_percent is not None:
                by_ear[row.ear] = int(row.wrs_percent)
        return by_ear

    async def _audiogram_id(
        self, user: CurrentUser, public_id: str | None
    ) -> int | None:
        if public_id is None:
            return None
        row = await AudiogramRepository(
            self._session, clinic_id=user.clinic_id
        ).get_detail(public_id)
        if row is None:
            raise ValidationError(reason="audiogram_not_found")
        return int(row.id)

    async def _tympanometry_id(
        self, user: CurrentUser, public_id: str | None
    ) -> int | None:
        if public_id is None:
            return None
        from ent.features.audiology.test_repository import TympanometryRepository

        row = await TympanometryRepository(
            self._session, clinic_id=user.clinic_id
        ).get_detail(public_id)
        if row is None:
            raise ValidationError(reason="tympanometry_not_found")
        return int(row.id)

    async def _require_device(self, user: CurrentUser, public_id: str) -> HearingDevice:
        row = await self._devices(user).get_detail(public_id)
        if row is None:
            raise HearingDeviceNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    def _devices(self, user: CurrentUser) -> HearingDeviceRepository:
        return HearingDeviceRepository(self._session, clinic_id=user.clinic_id)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)


def _is_refer(value: str | None) -> bool:
    return value == "refer"


def _aided_json(
    items: list[Any] | None,
) -> list[dict[str, int]] | None:
    if not items:
        return None
    return [
        {"frequency_hz": int(item.frequency_hz), "level_db": int(item.level_db)}
        for item in items
    ]


def _dates_json(dates: list[date] | None) -> list[str] | None:
    if not dates:
        return None
    return [value.isoformat() for value in dates]
