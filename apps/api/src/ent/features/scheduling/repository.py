"""Scheduling repositories."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, select

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.scheduling.constants import WAITING_ROOM_STATUSES
from ent.features.scheduling.models import Appointment, AppointmentType

# MySQL rejects NULLS LAST. `arrived_at IS NULL` sorts 0 before 1, so timed
# arrivals stay ahead of rows that have not arrived yet.
_WAITING_ROOM_ORDER = (
    Appointment.arrived_at.is_(None),
    Appointment.arrived_at.asc(),
    Appointment.starts_at.asc(),
)


class AppointmentTypeRepository(BaseRepository[AppointmentType]):
    model = AppointmentType

    async def get_by_code(self, code: str) -> AppointmentType | None:
        result = await self.session.execute(
            self._base_query().where(AppointmentType.code == code),
        )
        return result.scalar_one_or_none()


class AppointmentRepository(BaseRepository[Appointment]):
    model = Appointment

    async def list_in_range(
        self,
        *,
        starts_after: datetime,
        starts_before: datetime,
        doctor_user_id: int | None,
        room: str | None,
        site_id: int | None,
        page: PaginationParams | None,
    ) -> Page[Appointment]:
        resolved = normalize_pagination(page)
        stmt = self._base_query().where(
            Appointment.starts_at >= starts_after,
            Appointment.starts_at < starts_before,
        )
        if doctor_user_id is not None:
            stmt = stmt.where(Appointment.user_id == doctor_user_id)
        if room is not None:
            stmt = stmt.where(Appointment.room == room)
        if site_id is not None:
            stmt = stmt.where(Appointment.site_id == site_id)
        stmt = stmt.order_by(Appointment.starts_at.asc())
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery()),
            )
        ).scalar_one()
        stmt = apply_pagination(stmt, resolved)
        rows = list((await self.session.scalars(stmt)).all())
        from ent.core.repository.pagination import next_cursor_from_rows

        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=next_cursor_from_rows(rows, resolved),
        )

    async def list_waiting_room(
        self,
        *,
        site_id: int | None,
        day_start: datetime,
        day_end: datetime,
        page: PaginationParams | None,
    ) -> Page[Appointment]:
        resolved = normalize_pagination(page)
        stmt = (
            self._base_query()
            .where(
                Appointment.status.in_(tuple(WAITING_ROOM_STATUSES)),
                Appointment.starts_at >= day_start,
                Appointment.starts_at < day_end,
            )
            .order_by(*_WAITING_ROOM_ORDER)
        )
        if site_id is not None:
            stmt = stmt.where(Appointment.site_id == site_id)
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery()),
            )
        ).scalar_one()
        stmt = apply_pagination(stmt, resolved)
        rows = list((await self.session.scalars(stmt)).all())
        from ent.core.repository.pagination import next_cursor_from_rows

        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=next_cursor_from_rows(rows, resolved),
        )

    async def find_overlaps(
        self,
        *,
        doctor_user_id: int,
        starts_at: datetime,
        ends_at: datetime,
        exclude_appointment_id: int | None,
    ) -> list[Appointment]:
        stmt: Select[tuple[Appointment]] = self._base_query().where(
            Appointment.user_id == doctor_user_id,
            Appointment.status.notin_(("cancelled", "no_show")),
            Appointment.starts_at < ends_at,
            Appointment.ends_at > starts_at,
        )
        if exclude_appointment_id is not None:
            stmt = stmt.where(Appointment.id != exclude_appointment_id)
        stmt = stmt.order_by(Appointment.starts_at.asc())
        return list((await self.session.scalars(stmt)).all())
