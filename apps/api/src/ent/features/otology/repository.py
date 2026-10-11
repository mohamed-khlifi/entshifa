"""Tenant-scoped otology queries. Every read goes through ``_base_query()``."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.otology.models import EarDevice, OfficeProcedure, OtologyExam
from ent.features.procedures.models import ProcedureRecord
from ent.features.recalls.constants import OPEN_STATUSES
from ent.features.recalls.models import Recall

_DETAIL = (
    selectinload(OtologyExam.procedure_record).selectinload(ProcedureRecord.patient),
    selectinload(OtologyExam.procedure_record).selectinload(ProcedureRecord.encounter),
    selectinload(OtologyExam.procedure_record).selectinload(
        ProcedureRecord.procedure_concept
    ),
)


class OtologyRepository(BaseRepository[OtologyExam]):
    model = OtologyExam

    async def get_detail(self, public_id: str) -> OtologyExam | None:
        result = await self.session.execute(
            self._base_query()
            .where(OtologyExam.public_id == public_id)
            .options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def get_for_procedure(self, procedure_public_id: str) -> OtologyExam | None:
        result = await self.session.execute(
            self._base_query()
            .join(
                ProcedureRecord,
                OtologyExam.procedure_record_id == ProcedureRecord.id,
            )
            .where(
                ProcedureRecord.public_id == procedure_public_id,
                ProcedureRecord.clinic_id == self.clinic_id,
                ProcedureRecord.deleted_at.is_(None),
            )
            .options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def list_for_patient(
        self,
        patient_id: int,
        page: PaginationParams | None,
    ) -> Page[OtologyExam]:
        filtered = (
            self._base_query()
            .join(
                ProcedureRecord,
                OtologyExam.procedure_record_id == ProcedureRecord.id,
            )
            .where(
                ProcedureRecord.clinic_id == self.clinic_id,
                ProcedureRecord.patient_id == patient_id,
                ProcedureRecord.deleted_at.is_(None),
            )
        )
        resolved = normalize_pagination(page)
        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        stmt = filtered.options(*_DETAIL).order_by(
            ProcedureRecord.performed_at.desc(),
            OtologyExam.id.desc(),
        )
        rows = list(
            (await self.session.scalars(apply_pagination(stmt, resolved))).all()
        )
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=None,
        )


class OfficeProcedureRepository(BaseRepository[OfficeProcedure]):
    model = OfficeProcedure

    async def get_for_procedure(self, procedure_id: int) -> OfficeProcedure | None:
        result = await self.session.execute(
            self._base_query().where(
                OfficeProcedure.procedure_record_id == procedure_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_procedures(
        self, procedure_ids: list[int]
    ) -> list[OfficeProcedure]:
        if not procedure_ids:
            return []
        result = await self.session.scalars(
            self._base_query().where(
                OfficeProcedure.procedure_record_id.in_(procedure_ids)
            )
        )
        return list(result.all())


class EarDeviceRepository(BaseRepository[EarDevice]):
    model = EarDevice

    async def get_detail(self, public_id: str) -> EarDevice | None:
        result = await self.session.execute(
            self._base_query().where(EarDevice.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def list_for_patient(
        self,
        patient_id: int,
        page: PaginationParams | None,
    ) -> Page[EarDevice]:
        filtered = self._base_query().where(EarDevice.patient_id == patient_id)
        resolved = normalize_pagination(page)
        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        stmt = filtered.order_by(EarDevice.next_check_due.asc(), EarDevice.id.desc())
        rows = list(
            (await self.session.scalars(apply_pagination(stmt, resolved))).all()
        )
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=None,
        )

    async def list_for_inserted_procedure(self, procedure_id: int) -> list[EarDevice]:
        return await self.list_for_inserted_procedures([procedure_id])

    async def list_for_inserted_procedures(
        self, procedure_ids: list[int]
    ) -> list[EarDevice]:
        if not procedure_ids:
            return []
        result = await self.session.scalars(
            self._base_query().where(EarDevice.inserted_procedure_id.in_(procedure_ids))
        )
        return list(result.all())

    async def list_open_for_patient(self, patient_id: int) -> list[EarDevice]:
        result = await self.session.scalars(
            self._base_query().where(
                EarDevice.patient_id == patient_id,
                EarDevice.status.in_(("in_place", "blocked", "retained")),
            )
        )
        return list(result.all())


class ProcedureRecallRepository(BaseRepository[Recall]):
    model = Recall

    async def list_for_procedure(self, procedure_id: int) -> list[Recall]:
        result = await self.session.scalars(
            self._base_query().where(
                Recall.source_type == "procedure",
                Recall.source_id == procedure_id,
            )
        )
        return list(result.all())

    async def list_open_for_patient(self, patient_id: int) -> list[Recall]:
        result = await self.session.scalars(
            self._base_query().where(
                Recall.patient_id == patient_id,
                Recall.status.in_(tuple(OPEN_STATUSES)),
            )
        )
        return list(result.all())
