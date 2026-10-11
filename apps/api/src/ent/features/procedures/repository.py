"""Tenant-scoped procedure queries. Every read goes through ``_base_query()``."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.procedures.exceptions import (
    ProcedureInvalidTransitionError,
    ProcedureLockedError,
)
from ent.features.procedures.models import ProcedureRecord, ProcedureRecordAddendum

_DETAIL = (
    selectinload(ProcedureRecord.patient),
    selectinload(ProcedureRecord.encounter),
    selectinload(ProcedureRecord.procedure_concept),
    selectinload(ProcedureRecord.complication_concept),
    selectinload(ProcedureRecord.performed_by),
    selectinload(ProcedureRecord.signed_by),
    selectinload(ProcedureRecord.addenda).selectinload(ProcedureRecordAddendum.author),
)


class ProcedureRecordRepository(BaseRepository[ProcedureRecord]):
    model = ProcedureRecord

    def assert_draft(self, row: ProcedureRecord) -> None:
        """Reject any content write once the procedure has left draft."""

        if row.status != "draft":
            raise ProcedureLockedError(public_id=row.public_id, status=row.status)

    def mark_signed(
        self,
        row: ProcedureRecord,
        *,
        locked_hash: str,
        signed_at: datetime,
        signed_by_id: int,
        signed_role: str,
        signed_ip: bytes | None,
    ) -> None:
        self.assert_draft(row)
        row.status = "signed"
        row.locked_hash = locked_hash
        row.signed_at = signed_at
        row.signed_by_id = signed_by_id
        row.signed_role = signed_role
        row.signed_ip = signed_ip
        row.updated_by_id = signed_by_id
        row.version = int(row.version) + 1

    def mark_amended(self, row: ProcedureRecord, *, updated_by_id: int) -> None:
        if row.status not in {"signed", "amended"}:
            raise ProcedureInvalidTransitionError(
                from_status=row.status,
                to_status="amended",
            )
        row.status = "amended"
        row.updated_by_id = updated_by_id
        row.version = int(row.version) + 1

    async def get_detail(self, public_id: str) -> ProcedureRecord | None:
        result = await self.session.execute(
            self._base_query()
            .where(ProcedureRecord.public_id == public_id)
            .options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def list_procedures(
        self,
        page: PaginationParams | None,
        *,
        patient_id: int | None = None,
    ) -> Page[ProcedureRecord]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        if patient_id is not None:
            filtered = filtered.where(ProcedureRecord.patient_id == patient_id)
        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        stmt = filtered.options(*_DETAIL).order_by(
            ProcedureRecord.performed_at.desc(),
            ProcedureRecord.id.desc(),
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


class ProcedureRecordAddendumRepository(BaseRepository[ProcedureRecordAddendum]):
    model = ProcedureRecordAddendum
