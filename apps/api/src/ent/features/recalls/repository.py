"""Tenant-scoped recall queries. Every read goes through ``_base_query()``."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import joinedload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import (
    Page,
    apply_pagination,
    normalize_pagination,
)
from ent.core.schemas.base import PaginationParams
from ent.features.recalls.constants import UPCOMING_HORIZON_DAYS
from ent.features.recalls.models import Recall, RecallAction, RecallRequestIdempotency
from ent.features.recalls.schemas.requests import RecallBucket

_READ = (
    joinedload(Recall.patient),
    joinedload(Recall.appointment),
    joinedload(Recall.assigned_to),
)

_PAST_WINDOW = (
    "DATE_ADD(recall.due_on, INTERVAL recall.window_days DAY) < :recall_today"
)
_INSIDE_WINDOW = (
    "DATE_ADD(recall.due_on, INTERVAL recall.window_days DAY) >= :recall_today"
)


class RecallRepository(BaseRepository[Recall]):
    model = Recall

    def _scoped(
        self,
        *,
        today: date,
        bucket: RecallBucket | None,
        status: str | None,
        action_type: str | None,
        patient_id: int | None,
    ) -> Select[tuple[Recall]]:
        stmt = self._base_query()
        if patient_id is not None:
            stmt = stmt.where(Recall.patient_id == patient_id)
        if action_type is not None:
            stmt = stmt.where(Recall.action_type == action_type)
        past = text(_PAST_WINDOW)
        inside = text(_INSIDE_WINDOW)
        if bucket == "overdue" or status == "overdue":
            stmt = stmt.where(Recall.status == "pending", past)
        elif bucket == "upcoming":
            horizon = today + timedelta(days=UPCOMING_HORIZON_DAYS)
            stmt = stmt.where(
                Recall.status == "pending",
                Recall.due_on <= horizon,
                inside,
            )
        elif bucket == "unreachable":
            stmt = stmt.where(Recall.status == "unreachable")
        elif bucket == "active":
            stmt = stmt.where(Recall.status.in_(("pending", "booked", "unreachable")))
        elif status is not None:
            stmt = stmt.where(Recall.status == status)
        return stmt.params(recall_today=today)

    async def list_recalls(
        self,
        *,
        today: date,
        bucket: RecallBucket | None,
        status: str | None,
        action_type: str | None,
        patient_id: int | None,
        page: PaginationParams | None,
    ) -> Page[Recall]:
        resolved = normalize_pagination(page)
        filtered = self._scoped(
            today=today,
            bucket=bucket,
            status=status,
            action_type=action_type,
            patient_id=patient_id,
        )
        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        stmt = apply_pagination(
            filtered.options(*_READ).order_by(Recall.due_on.asc(), Recall.id.asc()),
            resolved,
        )
        rows = list((await self.session.scalars(stmt)).unique().all())
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=None,
        )

    async def get_for_read(self, public_id: str) -> Recall | None:
        result = await self.session.scalars(
            self._base_query().where(Recall.public_id == public_id).options(*_READ)
        )
        return result.unique().one_or_none()

    async def summary(self, *, today: date) -> tuple[int, int, int, int]:
        overdue = await self._count(today=today, bucket="overdue")
        upcoming = await self._count(today=today, bucket="upcoming")
        unreachable = await self._count(today=today, bucket="unreachable")
        active = await self._count(today=today, bucket="active")
        return overdue, upcoming, unreachable, active

    async def _count(self, *, today: date, bucket: RecallBucket) -> int:
        filtered = self._scoped(
            today=today,
            bucket=bucket,
            status=None,
            action_type=None,
            patient_id=None,
        )
        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        return int(total or 0)


class RecallActionRepository(BaseRepository[RecallAction]):
    model = RecallAction


class RecallIdempotencyRepository(BaseRepository[RecallRequestIdempotency]):
    model = RecallRequestIdempotency

    async def get_by_key(self, key: str) -> RecallRequestIdempotency | None:
        result = await self.session.execute(
            self._base_query().where(RecallRequestIdempotency.idempotency_key == key)
        )
        return result.scalar_one_or_none()
