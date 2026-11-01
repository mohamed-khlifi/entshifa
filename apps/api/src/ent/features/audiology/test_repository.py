"""Repositories for speech, tympanometry, OAE and ABR (P4-03)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.audiology.models import Audiogram
from ent.features.audiology.schemas.test_requests import AcousticReflexInput
from ent.features.audiology.test_records import (
    AbrResult,
    AcousticReflex,
    OaeResult,
    SpeechAudiometry,
    Tympanometry,
)

_SPEECH_LOAD = (
    selectinload(SpeechAudiometry.patient),
    selectinload(SpeechAudiometry.encounter),
    selectinload(SpeechAudiometry.audiogram),
    selectinload(SpeechAudiometry.performed_by),
)

_TYMP_LOAD = (
    selectinload(Tympanometry.patient),
    selectinload(Tympanometry.encounter),
    selectinload(Tympanometry.performed_by),
    selectinload(Tympanometry.overridden_by),
    selectinload(Tympanometry.reflexes),
)

_OAE_LOAD = (
    selectinload(OaeResult.patient),
    selectinload(OaeResult.encounter),
    selectinload(OaeResult.performed_by),
)

_ABR_LOAD = (
    selectinload(AbrResult.patient),
    selectinload(AbrResult.encounter),
    selectinload(AbrResult.performed_by),
)


class SpeechAudiometryRepository(BaseRepository[SpeechAudiometry]):
    model = SpeechAudiometry

    async def get_detail(self, public_id: str) -> SpeechAudiometry | None:
        result = await self.session.scalars(
            self._base_query()
            .where(SpeechAudiometry.public_id == public_id)
            .options(*_SPEECH_LOAD)
        )
        return result.one_or_none()

    async def list_for_patient(
        self,
        page: PaginationParams,
        *,
        patient_id: int | None = None,
        encounter_id: int | None = None,
        audiogram_id: int | None = None,
    ) -> Page[SpeechAudiometry]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        if patient_id is not None:
            filtered = filtered.where(SpeechAudiometry.patient_id == patient_id)
        if encounter_id is not None:
            filtered = filtered.where(SpeechAudiometry.encounter_id == encounter_id)
        if audiogram_id is not None:
            filtered = filtered.where(SpeechAudiometry.audiogram_id == audiogram_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_SPEECH_LOAD).order_by(
                            SpeechAudiometry.performed_at.is_(None),
                            SpeechAudiometry.performed_at.desc(),
                            SpeechAudiometry.id.desc(),
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def list_for_audiogram(self, audiogram_id: int) -> list[SpeechAudiometry]:
        result = await self.session.scalars(
            self._base_query().where(SpeechAudiometry.audiogram_id == audiogram_id)
        )
        return list(result.all())

    async def latest_wrs_by_ear(
        self, *, patient_id: int, audiogram_id: int | None
    ) -> dict[str, tuple[int | None, int | None]]:
        """Return latest SRT and WRS per ear for asymmetry (patient or audiogram scope)."""

        filtered = self._base_query().where(SpeechAudiometry.patient_id == patient_id)
        if audiogram_id is not None:
            filtered = filtered.where(SpeechAudiometry.audiogram_id == audiogram_id)
        rows = list(
            (
                await self.session.scalars(
                    filtered.order_by(
                        SpeechAudiometry.performed_at.desc(),
                        SpeechAudiometry.id.desc(),
                    )
                )
            ).all()
        )
        out: dict[str, tuple[int | None, int | None]] = {
            "right": (None, None),
            "left": (None, None),
        }
        for row in rows:
            if out[row.ear][0] is None and row.srt_db is not None:
                out[row.ear] = (row.srt_db, out[row.ear][1])
            if out[row.ear][1] is None and row.wrs_percent is not None:
                out[row.ear] = (out[row.ear][0], row.wrs_percent)
            if all(v is not None for v in out["right"]) and all(
                v is not None for v in out["left"]
            ):
                break
        return out


class TympanometryRepository(BaseRepository[Tympanometry]):
    model = Tympanometry

    async def get_detail(self, public_id: str) -> Tympanometry | None:
        result = await self.session.scalars(
            self._base_query()
            .where(Tympanometry.public_id == public_id)
            .options(*_TYMP_LOAD)
        )
        return result.one_or_none()

    async def list_for_patient(
        self,
        page: PaginationParams,
        *,
        patient_id: int | None = None,
        encounter_id: int | None = None,
    ) -> Page[Tympanometry]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        if patient_id is not None:
            filtered = filtered.where(Tympanometry.patient_id == patient_id)
        if encounter_id is not None:
            filtered = filtered.where(Tympanometry.encounter_id == encounter_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_TYMP_LOAD).order_by(
                            Tympanometry.performed_at.is_(None),
                            Tympanometry.performed_at.desc(),
                            Tympanometry.id.desc(),
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def sync_reflexes(
        self,
        row: Tympanometry,
        inputs: list[AcousticReflexInput],
        *,
        user_id: int,
    ) -> None:
        existing = list(
            (
                await self.session.scalars(
                    select(AcousticReflex).where(
                        AcousticReflex.clinic_id == self.clinic_id,
                        AcousticReflex.tympanometry_id == int(row.id),
                    )
                )
            ).all()
        )
        desired_keys = {
            (item.stimulus_ear, item.mode, item.frequency_hz) for item in inputs
        }
        by_key = {(r.stimulus_ear, r.mode, int(r.frequency_hz)): r for r in existing}
        now = datetime.now(UTC).replace(tzinfo=None)
        for item in inputs:
            key = (item.stimulus_ear, item.mode, item.frequency_hz)
            reflex = by_key.get(key)
            if reflex is None:
                self.session.add(
                    AcousticReflex(
                        clinic_id=self.clinic_id,
                        tympanometry_id=int(row.id),
                        stimulus_ear=item.stimulus_ear,
                        mode=item.mode,
                        frequency_hz=item.frequency_hz,
                        threshold_db=item.threshold_db,
                        status=item.status,
                        created_by_id=user_id,
                        updated_by_id=user_id,
                    )
                )
                continue
            reflex.deleted_at = None
            reflex.deleted_by_id = None
            reflex.threshold_db = item.threshold_db
            reflex.status = item.status
            reflex.updated_by_id = user_id
        for existing_key, reflex in by_key.items():
            if existing_key in desired_keys:
                continue
            if reflex.deleted_at is not None:
                continue
            reflex.deleted_at = now
            reflex.deleted_by_id = user_id
            reflex.updated_by_id = user_id


class OaeResultRepository(BaseRepository[OaeResult]):
    model = OaeResult

    async def get_detail(self, public_id: str) -> OaeResult | None:
        result = await self.session.scalars(
            self._base_query()
            .where(OaeResult.public_id == public_id)
            .options(*_OAE_LOAD)
        )
        return result.one_or_none()

    async def list_for_patient(
        self,
        page: PaginationParams,
        *,
        patient_id: int | None = None,
        encounter_id: int | None = None,
    ) -> Page[OaeResult]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        if patient_id is not None:
            filtered = filtered.where(OaeResult.patient_id == patient_id)
        if encounter_id is not None:
            filtered = filtered.where(OaeResult.encounter_id == encounter_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_OAE_LOAD).order_by(
                            OaeResult.performed_at.is_(None),
                            OaeResult.performed_at.desc(),
                            OaeResult.id.desc(),
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )


class AbrResultRepository(BaseRepository[AbrResult]):
    model = AbrResult

    async def get_detail(self, public_id: str) -> AbrResult | None:
        result = await self.session.scalars(
            self._base_query()
            .where(AbrResult.public_id == public_id)
            .options(*_ABR_LOAD)
        )
        return result.one_or_none()

    async def list_for_patient(
        self,
        page: PaginationParams,
        *,
        patient_id: int | None = None,
        encounter_id: int | None = None,
    ) -> Page[AbrResult]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        if patient_id is not None:
            filtered = filtered.where(AbrResult.patient_id == patient_id)
        if encounter_id is not None:
            filtered = filtered.where(AbrResult.encounter_id == encounter_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_ABR_LOAD).order_by(
                            AbrResult.performed_at.is_(None),
                            AbrResult.performed_at.desc(),
                            AbrResult.id.desc(),
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def find_contralateral_wave_v(
        self,
        *,
        patient_id: int,
        ear: str,
        performed_at: datetime,
        exclude_id: int | None = None,
    ) -> AbrResult | None:
        opposite = "left" if ear == "right" else "right"
        filtered = self._base_query().where(
            AbrResult.patient_id == patient_id,
            AbrResult.ear == opposite,
            AbrResult.wave_v_ms.is_not(None),
        )
        if exclude_id is not None:
            filtered = filtered.where(AbrResult.id != exclude_id)
        result = await self.session.scalars(
            filtered.order_by(
                AbrResult.performed_at.desc(),
                AbrResult.id.desc(),
            )
        )
        for row in result.all():
            return row
        return None


class AudiogramLinkRepository(BaseRepository[Audiogram]):
    model = Audiogram

    async def get_internal_id(self, public_id: str) -> int | None:
        row = await self.get_by_public_id(public_id)
        return int(row.id) if row is not None else None
