"""Repositories for hearing devices and pediatric audiology (P4-06)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

import ent.features.audiology.models  # noqa: F401 — register Audiogram for OmeEpisode relationships
import ent.features.audiology.test_records  # noqa: F401 — register Tympanometry
from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.audiology.device_models import (
    HearingDevice,
    OmeEpisode,
    PediatricAudiologyRecord,
)

_DEVICE_LOAD = (selectinload(HearingDevice.patient),)
_PEDIATRIC_LOAD = (
    selectinload(PediatricAudiologyRecord.patient),
    selectinload(PediatricAudiologyRecord.ha_candidacy_confirmed_by),
    selectinload(PediatricAudiologyRecord.ci_candidacy_confirmed_by),
)
_OME_LOAD = (
    selectinload(OmeEpisode.patient),
    selectinload(OmeEpisode.encounter),
    selectinload(OmeEpisode.audiogram),
    selectinload(OmeEpisode.tympanometry),
)


class HearingDeviceRepository(BaseRepository[HearingDevice]):
    model = HearingDevice

    async def get_detail(self, public_id: str) -> HearingDevice | None:
        return (
            await self.session.scalars(
                self._base_query()
                .where(HearingDevice.public_id == public_id)
                .options(*_DEVICE_LOAD)
            )
        ).one_or_none()

    async def list_for_patient(
        self,
        patient_id: int,
        page: PaginationParams,
    ) -> Page[HearingDevice]:
        resolved = normalize_pagination(page)
        filtered = self._base_query().where(HearingDevice.patient_id == patient_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_DEVICE_LOAD).order_by(
                            HearingDevice.fitted_on.is_(None),
                            HearingDevice.fitted_on.desc(),
                            HearingDevice.id.desc(),
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

    async def list_active_for_patient(self, patient_id: int) -> list[HearingDevice]:
        return list(
            (
                await self.session.scalars(
                    self._base_query()
                    .where(
                        HearingDevice.patient_id == patient_id,
                        HearingDevice.status.in_(("active", "trial")),
                    )
                    .order_by(HearingDevice.ear, HearingDevice.id.desc())
                )
            ).all()
        )


class PediatricAudiologyRepository(BaseRepository[PediatricAudiologyRecord]):
    model = PediatricAudiologyRecord

    async def get_for_patient(self, patient_id: int) -> PediatricAudiologyRecord | None:
        return (
            await self.session.scalars(
                self._base_query()
                .where(PediatricAudiologyRecord.patient_id == patient_id)
                .options(*_PEDIATRIC_LOAD)
            )
        ).one_or_none()


class OmeEpisodeRepository(BaseRepository[OmeEpisode]):
    model = OmeEpisode

    async def get_detail(self, public_id: str) -> OmeEpisode | None:
        return (
            await self.session.scalars(
                self._base_query()
                .where(OmeEpisode.public_id == public_id)
                .options(*_OME_LOAD)
            )
        ).one_or_none()

    async def list_for_patient(
        self,
        patient_id: int,
        page: PaginationParams,
    ) -> Page[OmeEpisode]:
        resolved = normalize_pagination(page)
        filtered = self._base_query().where(OmeEpisode.patient_id == patient_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(*_OME_LOAD).order_by(
                            OmeEpisode.first_seen_on.desc(),
                            OmeEpisode.id.desc(),
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

    async def list_open_watchful_waiting(self, patient_id: int) -> list[OmeEpisode]:
        return list(
            (
                await self.session.scalars(
                    self._base_query().where(
                        OmeEpisode.patient_id == patient_id,
                        OmeEpisode.status == "watchful_waiting",
                    )
                )
            ).all()
        )
