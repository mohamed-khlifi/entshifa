"""Speech audiometry use cases (P4-03)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.audiology.constants import SPEECH_RESOURCE_CREATE
from ent.features.audiology.exceptions import (
    AudiogramNotFoundError,
    AudiogramVersionConflictError,
    SpeechAudiometryNotFoundError,
)
from ent.features.audiology.idempotency_util import replay_idempotent, store_idempotent
from ent.features.audiology.mapping import to_page
from ent.features.audiology.references import AudiologyReferences
from ent.features.audiology.repository import AudiogramRepository
from ent.features.audiology.schemas.test_requests import (
    SpeechAudiometryCreate,
    SpeechAudiometryUpdate,
)
from ent.features.audiology.schemas.test_responses import SpeechAudiometryRead
from ent.features.audiology.speech_audiogram_sync import sync_audiogram_for_speech
from ent.features.audiology.test_mapping import speech_read
from ent.features.audiology.test_records import SpeechAudiometry
from ent.features.audiology.test_repository import SpeechAudiometryRepository
from ent.features.encounters.repository import EncounterRepository
from ent.features.procedures.mapping import blank_to_none, to_utc_naive


class SpeechAudiometryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = AudiologyReferences(session)

    async def create_speech_audiometry(
        self,
        *,
        user: CurrentUser,
        body: SpeechAudiometryCreate,
        idempotency_key: str | None,
    ) -> SpeechAudiometryRead:
        self._bind(user)
        replay = await replay_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=SPEECH_RESOURCE_CREATE,
        )
        if replay is not None:
            return await self.get_speech_audiometry(user=user, public_id=replay)
        patient = await self._refs.patient(user, body.patient_public_id)
        audiogram_id = await self._audiogram_id(
            user, body.audiogram_public_id, patient_id=int(patient.id)
        )
        performed_at = body.performed_at or datetime.now(UTC).replace(tzinfo=None)
        performer = body.performed_by_public_id or user.user_public_id
        row = SpeechAudiometry(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user, body.encounter_public_id, patient_id=int(patient.id)
            ),
            audiogram_id=audiogram_id,
            performed_at=to_utc_naive(performed_at),
            performed_by_id=await self._refs.member_id(user, performer),
            ear=body.ear,
            srt_db=body.srt_db,
            sdt_db=body.sdt_db,
            wrs_percent=body.wrs_percent,
            wrs_level_db=body.wrs_level_db,
            additional_wrs_points=(
                [item.model_dump(mode="json") for item in body.additional_wrs_points]
                if body.additional_wrs_points
                else None
            ),
            word_list=blank_to_none(body.word_list),
            list_locale=blank_to_none(body.list_locale),
            mcl_db=body.mcl_db,
            ucl_db=body.ucl_db,
            rollover=body.rollover,
            sin_test=blank_to_none(body.sin_test),
            sin_snr_db=body.sin_snr_db,
            sin_score_percent=body.sin_score_percent,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._repo(user).add(row)
        await self._session.flush()
        if audiogram_id is not None:
            await sync_audiogram_for_speech(
                self._session, user, audiogram_id=audiogram_id
            )
        await store_idempotent(
            self._session,
            user,
            key=idempotency_key,
            body=body,
            resource_type=SPEECH_RESOURCE_CREATE,
            resource_public_id=row.public_id,
        )
        await self._session.commit()
        return await self.get_speech_audiometry(user=user, public_id=row.public_id)

    async def get_speech_audiometry(
        self, *, user: CurrentUser, public_id: str
    ) -> SpeechAudiometryRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._audit.record_access(
            action="get",
            entity_type="speech_audiometry",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        loaded = await self._repo(user).get_detail(public_id)
        if loaded is None:
            raise SpeechAudiometryNotFoundError(public_id=public_id)
        return speech_read(loaded)

    async def list_speech_audiometry(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        patient_public_id: str | None = None,
        encounter_public_id: str | None = None,
        audiogram_public_id: str | None = None,
    ) -> PageSchema[SpeechAudiometryRead]:
        self._bind(user)
        patient_id, encounter_id, audiogram_id = await self._list_filters(
            user,
            patient_public_id=patient_public_id,
            encounter_public_id=encounter_public_id,
            audiogram_public_id=audiogram_public_id,
        )
        result = await self._repo(user).list_for_patient(
            page,
            patient_id=patient_id,
            encounter_id=encounter_id,
            audiogram_id=audiogram_id,
        )
        items = [speech_read(row) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="speech_audiometry",
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

    async def update_speech_audiometry(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: SpeechAudiometryUpdate,
    ) -> SpeechAudiometryRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        previous_audiogram_id = row.audiogram_id
        if body.encounter_public_id is not None:
            row.encounter_id = await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(row.patient_id),
            )
        if body.audiogram_public_id is not None:
            row.audiogram_id = await self._audiogram_id(
                user,
                body.audiogram_public_id,
                patient_id=int(row.patient_id),
            )
        if body.performed_at is not None:
            row.performed_at = to_utc_naive(body.performed_at)
        if body.performed_by_public_id is not None:
            row.performed_by_id = await self._refs.member_id(
                user, body.performed_by_public_id
            )
        data = body.model_dump(exclude_unset=True)
        for field in (
            "srt_db",
            "sdt_db",
            "wrs_percent",
            "wrs_level_db",
            "mcl_db",
            "ucl_db",
            "rollover",
            "sin_snr_db",
            "sin_score_percent",
        ):
            if field in data:
                setattr(row, field, data[field])
        if "word_list" in data:
            row.word_list = blank_to_none(body.word_list)
        if "list_locale" in data:
            row.list_locale = blank_to_none(body.list_locale)
        if "sin_test" in data:
            row.sin_test = blank_to_none(body.sin_test)
        if body.additional_wrs_points is not None:
            row.additional_wrs_points = [
                item.model_dump(mode="json") for item in body.additional_wrs_points
            ]
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.flush()
        for audiogram_id in {previous_audiogram_id, row.audiogram_id}:
            if audiogram_id is not None:
                await sync_audiogram_for_speech(
                    self._session, user, audiogram_id=int(audiogram_id)
                )
        await self._session.commit()
        return await self.get_speech_audiometry(user=user, public_id=row.public_id)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _repo(self, user: CurrentUser) -> SpeechAudiometryRepository:
        return SpeechAudiometryRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> SpeechAudiometry:
        row = await self._repo(user).get_detail(public_id)
        if row is None:
            raise SpeechAudiometryNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    def _check_version(self, row: SpeechAudiometry, version: int) -> None:
        if int(row.version) != version:
            raise AudiogramVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )

    async def _audiogram_id(
        self,
        user: CurrentUser,
        public_id: str | None,
        *,
        patient_id: int,
    ) -> int | None:
        if public_id is None:
            return None
        row = await AudiogramRepository(
            self._session, clinic_id=user.clinic_id
        ).get_detail(public_id)
        if row is None:
            raise AudiogramNotFoundError(public_id=public_id)
        if int(row.patient_id) != patient_id:
            raise ValidationError(reason="audiogram_patient", audiogramId=public_id)
        return int(row.id)

    async def _list_filters(
        self,
        user: CurrentUser,
        *,
        patient_public_id: str | None,
        encounter_public_id: str | None,
        audiogram_public_id: str | None,
    ) -> tuple[int | None, int | None, int | None]:
        patient_id = None
        encounter_id = None
        audiogram_id = None
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
        if audiogram_public_id is not None:
            audiogram_id = await self._audiogram_id(
                user, audiogram_public_id, patient_id=patient_id or 0
            )
            if patient_id is None and audiogram_id is not None:
                ag = await AudiogramRepository(
                    self._session, clinic_id=user.clinic_id
                ).get_detail_by_id(audiogram_id)
                if ag is not None:
                    patient_id = int(ag.patient_id)
        return patient_id, encounter_id, audiogram_id
