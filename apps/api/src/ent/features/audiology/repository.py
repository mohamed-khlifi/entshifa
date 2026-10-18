"""Audiogram queries. Every list goes through ``_base_query()``."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.audiology.models import (
    Audiogram,
    AudiogramThreshold,
    AudiologyRequestIdempotency,
)
from ent.features.audiology.schemas.requests import ThresholdInput

_LOAD = (
    selectinload(Audiogram.thresholds),
    selectinload(Audiogram.patient),
    selectinload(Audiogram.encounter),
    selectinload(Audiogram.performed_by),
    selectinload(Audiogram.baseline_audiogram),
)


class AudiogramRepository(BaseRepository[Audiogram]):
    model = Audiogram

    async def get_detail(self, public_id: str) -> Audiogram | None:
        result = await self.session.scalars(
            self._base_query().where(Audiogram.public_id == public_id).options(*_LOAD)
        )
        return result.one_or_none()

    async def list_audiograms(
        self,
        page: PaginationParams,
        *,
        patient_id: int | None = None,
        encounter_id: int | None = None,
    ) -> Page[Audiogram]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        if patient_id is not None:
            filtered = filtered.where(Audiogram.patient_id == patient_id)
        if encounter_id is not None:
            filtered = filtered.where(Audiogram.encounter_id == encounter_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_LOAD).order_by(
                            Audiogram.performed_at.is_(None),
                            Audiogram.performed_at.desc(),
                            Audiogram.id.desc(),
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

    async def clear_other_baselines(
        self,
        *,
        patient_id: int,
        keep_audiogram_id: int,
    ) -> None:
        rows = list(
            (
                await self.session.scalars(
                    self._base_query().where(
                        Audiogram.patient_id == patient_id,
                        Audiogram.is_baseline.is_(True),
                        Audiogram.id != keep_audiogram_id,
                    )
                )
            ).all()
        )
        for row in rows:
            row.is_baseline = False

    async def sync_thresholds(
        self,
        audiogram: Audiogram,
        inputs: list[ThresholdInput],
        *,
        user_id: int,
    ) -> None:
        existing = list(
            (
                await self.session.scalars(
                    select(AudiogramThreshold).where(
                        AudiogramThreshold.clinic_id == self.clinic_id,
                        AudiogramThreshold.audiogram_id == int(audiogram.id),
                    )
                )
            ).all()
        )
        desired_keys = {
            (item.ear, item.conduction, item.frequency_hz, item.is_masked)
            for item in inputs
        }
        by_key = {
            (row.ear, row.conduction, int(row.frequency_hz), bool(row.is_masked)): row
            for row in existing
        }
        now = datetime.now(UTC).replace(tzinfo=None)
        for item in inputs:
            key = (item.ear, item.conduction, item.frequency_hz, item.is_masked)
            row = by_key.get(key)
            if row is None:
                self.session.add(
                    AudiogramThreshold(
                        clinic_id=self.clinic_id,
                        audiogram_id=int(audiogram.id),
                        ear=item.ear,
                        conduction=item.conduction,
                        frequency_hz=item.frequency_hz,
                        level_db=item.level_db,
                        is_masked=item.is_masked,
                        is_no_response=item.is_no_response,
                        created_by_id=user_id,
                        updated_by_id=user_id,
                    )
                )
                continue
            row.deleted_at = None
            row.deleted_by_id = None
            row.level_db = item.level_db
            row.is_no_response = item.is_no_response
            row.updated_by_id = user_id
        for existing_key, row in by_key.items():
            if existing_key in desired_keys:
                continue
            if row.deleted_at is not None:
                continue
            row.deleted_at = now
            row.deleted_by_id = user_id
            row.updated_by_id = user_id


class AudiologyIdempotencyRepository(BaseRepository[AudiologyRequestIdempotency]):
    model = AudiologyRequestIdempotency

    async def get_by_key(self, key: str) -> AudiologyRequestIdempotency | None:
        result = await self.session.scalars(
            self._base_query().where(AudiologyRequestIdempotency.idempotency_key == key)
        )
        return result.one_or_none()
