"""Tenant-scoped instrument queries."""

from __future__ import annotations

from sqlalchemy import Select, and_, false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import (
    Page,
    normalize_pagination,
)
from ent.core.schemas.base import PaginationParams
from ent.features.questionnaires.models import (
    Instrument,
    InstrumentVersion,
)

_DETAIL_LOAD = (
    selectinload(Instrument.versions).selectinload(InstrumentVersion.items),
    selectinload(Instrument.versions).selectinload(InstrumentVersion.options),
    selectinload(Instrument.versions).selectinload(InstrumentVersion.translations),
)


class InstrumentRepository(BaseRepository[Instrument]):
    model = Instrument

    def _base_query(self) -> Select[tuple[Instrument]]:
        stmt = select(self.model).where(self.model.deleted_at.is_(None))
        if self.clinic_id is None:
            return stmt.where(false())
        return stmt.where(
            or_(
                self.model.clinic_id == self.clinic_id,
                and_(
                    self.model.clinic_id.is_(None),
                    self.model.is_system.is_(True),
                ),
            )
        )

    async def get_by_code(self, code: str) -> Instrument | None:
        result = await self.session.execute(
            self._base_query()
            .where(
                self.model.code == code,
                self.model.is_active.is_(True),
            )
            .order_by(self.model.clinic_id.is_(None))
        )
        return result.scalars().first()

    async def get_for_read(self, public_id: str) -> Instrument | None:
        result = await self.session.scalars(
            self._base_query()
            .where(Instrument.public_id == public_id)
            .options(*_DETAIL_LOAD)
        )
        return result.unique().one_or_none()

    async def get_clinic_owned_by_code(self, code: str) -> Instrument | None:
        result = await self.session.execute(
            self._base_query().where(
                self.model.code == code,
                self.model.clinic_id == self.clinic_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_effective(
        self,
        *,
        category: str | None,
        respondent: str | None,
        page: PaginationParams | None,
    ) -> Page[Instrument]:
        resolved = normalize_pagination(page)
        stmt = self._base_query().where(self.model.is_active.is_(True))
        if category is not None:
            stmt = stmt.where(self.model.category == category)
        if respondent is not None:
            stmt = stmt.where(self.model.respondent == respondent)
        rows = list((await self.session.scalars(stmt)).unique().all())
        effective_by_code: dict[str, Instrument] = {}
        for row in rows:
            current = effective_by_code.get(row.code)
            if current is None or row.clinic_id == self.clinic_id:
                effective_by_code[row.code] = row
        effective = [effective_by_code[code] for code in sorted(effective_by_code)]
        total = len(effective)
        start = int(resolved.offset or 0)
        end = start + int(resolved.limit)
        page_rows = effective[start:end]
        if page_rows:
            ids = [int(row.id) for row in page_rows]
            hydrated = await self.session.scalars(
                select(Instrument)
                .where(Instrument.id.in_(ids))
                .options(
                    selectinload(Instrument.versions).selectinload(
                        InstrumentVersion.translations
                    ),
                )
            )
            by_id = {int(row.id): row for row in hydrated.unique().all()}
            page_rows = [
                by_id[int(row.id)] for row in page_rows if int(row.id) in by_id
            ]
        return Page(
            items=page_rows,
            total=total,
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=None,
        )


class InstrumentVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_current(self, instrument_id: int) -> InstrumentVersion | None:
        result = await self.session.scalars(
            select(InstrumentVersion)
            .where(
                InstrumentVersion.deleted_at.is_(None),
                InstrumentVersion.instrument_id == instrument_id,
                InstrumentVersion.is_current.is_(True),
            )
            .options(
                selectinload(InstrumentVersion.items),
                selectinload(InstrumentVersion.options),
                selectinload(InstrumentVersion.translations),
            )
            .order_by(InstrumentVersion.effective_from.desc())
            .limit(1)
        )
        return result.unique().one_or_none()

    async def clear_current(self, instrument_id: int) -> None:
        rows = (
            await self.session.scalars(
                select(InstrumentVersion).where(
                    InstrumentVersion.instrument_id == instrument_id,
                    InstrumentVersion.is_current.is_(True),
                    InstrumentVersion.deleted_at.is_(None),
                )
            )
        ).all()
        for row in rows:
            row.is_current = False
