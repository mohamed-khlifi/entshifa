"""Tenant-scoped short-procedure queries. Every read uses ``_base_query()``."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.office_procedures.constants import SHORT_OFFICE_SUBTYPES
from ent.features.otology.models import OfficeProcedure
from ent.features.procedures.models import ProcedureRecord
from ent.features.recalls.models import Recall

_DETAIL = (
    selectinload(OfficeProcedure.procedure_record).selectinload(
        ProcedureRecord.patient
    ),
    selectinload(OfficeProcedure.procedure_record).selectinload(
        ProcedureRecord.encounter
    ),
    selectinload(OfficeProcedure.procedure_record).selectinload(
        ProcedureRecord.procedure_concept
    ),
)


class ShortOfficeProcedureRepository(BaseRepository[OfficeProcedure]):
    model = OfficeProcedure

    async def get_detail(self, public_id: str) -> OfficeProcedure | None:
        result = await self.session.execute(
            self._base_query()
            .where(
                OfficeProcedure.public_id == public_id,
                OfficeProcedure.subtype.in_(SHORT_OFFICE_SUBTYPES),
            )
            .options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def get_for_procedure(
        self, procedure_public_id: str
    ) -> OfficeProcedure | None:
        result = await self.session.execute(
            self._base_query()
            .join(
                ProcedureRecord,
                OfficeProcedure.procedure_record_id == ProcedureRecord.id,
            )
            .where(
                ProcedureRecord.public_id == procedure_public_id,
                ProcedureRecord.clinic_id == self.clinic_id,
                ProcedureRecord.deleted_at.is_(None),
                OfficeProcedure.subtype.in_(SHORT_OFFICE_SUBTYPES),
            )
            .options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def list_for_patient(
        self,
        patient_id: int,
        page: PaginationParams | None,
    ) -> Page[OfficeProcedure]:
        filtered = (
            self._base_query()
            .join(
                ProcedureRecord,
                OfficeProcedure.procedure_record_id == ProcedureRecord.id,
            )
            .where(
                ProcedureRecord.clinic_id == self.clinic_id,
                ProcedureRecord.patient_id == patient_id,
                ProcedureRecord.deleted_at.is_(None),
                OfficeProcedure.subtype.in_(SHORT_OFFICE_SUBTYPES),
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
            OfficeProcedure.id.desc(),
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
