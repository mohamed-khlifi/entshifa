"""Tenant-scoped laryngoscopy queries. Every read goes through ``_base_query()``."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.laryngoscopy.models import LaryngoscopyExam
from ent.features.procedures.models import ProcedureRecord

_DETAIL = (
    selectinload(LaryngoscopyExam.procedure_record).selectinload(
        ProcedureRecord.patient
    ),
    selectinload(LaryngoscopyExam.procedure_record).selectinload(
        ProcedureRecord.encounter
    ),
)


class LaryngoscopyRepository(BaseRepository[LaryngoscopyExam]):
    model = LaryngoscopyExam

    async def get_detail(self, public_id: str) -> LaryngoscopyExam | None:
        result = await self.session.execute(
            self._base_query()
            .where(LaryngoscopyExam.public_id == public_id)
            .options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def get_for_procedure(
        self, procedure_public_id: str
    ) -> LaryngoscopyExam | None:
        result = await self.session.execute(
            self._base_query()
            .join(
                ProcedureRecord,
                LaryngoscopyExam.procedure_record_id == ProcedureRecord.id,
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
    ) -> Page[LaryngoscopyExam]:
        filtered = (
            self._base_query()
            .join(
                ProcedureRecord,
                LaryngoscopyExam.procedure_record_id == ProcedureRecord.id,
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
            LaryngoscopyExam.id.desc(),
        )
        rows = list(
            (await self.session.scalars(apply_pagination(stmt, resolved))).all()
        )
        return Page(
            items=rows,
            total=int(total),
            limit=resolved.limit,
            offset=resolved.offset,
        )
