"""Generic tenant-scoped repository (architecture section 7.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Generic, TypeVar

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ent.core.repository.filters import FilterSet, apply_filters
from ent.core.repository.pagination import (
    Page,
    apply_pagination,
    apply_sort,
    next_cursor_from_rows,
    normalize_pagination,
)
from ent.core.schemas.base import PaginationParams

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class BaseRepository(Generic[ModelT]):
    """All clinical queries must go through ``_base_query()`` — never bypass it."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession, clinic_id: int | None = None) -> None:
        self.session = session
        self.clinic_id = clinic_id

    def _base_query(self) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        if self.clinic_id is not None and hasattr(self.model, "clinic_id"):
            stmt = stmt.where(self.model.clinic_id == self.clinic_id)  # type: ignore[attr-defined]
        return stmt

    async def get(self, id_: int) -> ModelT | None:
        result = await self.session.execute(
            self._base_query().where(self.model.id == id_),  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: str) -> ModelT | None:
        result = await self.session.execute(
            self._base_query().where(self.model.public_id == public_id),  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        filters: FilterSet | None = None,
        sort: str | None = None,
        page: PaginationParams | None = None,
    ) -> Page[ModelT]:
        resolved = normalize_pagination(page)
        stmt = apply_filters(self._base_query(), self.model, filters)
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()
        stmt = apply_sort(stmt, self.model, sort)
        stmt = apply_pagination(stmt, resolved)
        rows = list((await self.session.scalars(stmt)).all())
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=next_cursor_from_rows(rows, resolved),
        )

    async def add(self, entity: ModelT) -> ModelT:
        if (
            self.clinic_id is not None
            and hasattr(entity, "clinic_id")
            and getattr(entity, "clinic_id", None) is None
        ):
            entity.clinic_id = self.clinic_id
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def soft_delete(self, id_: int, by_user_id: int) -> None:
        if not hasattr(self.model, "deleted_at"):
            msg = f"{self.model.__name__} does not support soft delete"
            raise TypeError(msg)
        stmt = (
            update(self.model)
            .where(
                self.model.id == id_,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .values(
                deleted_at=datetime.now(UTC).replace(tzinfo=None),
                deleted_by_id=by_user_id,
            )
        )
        if self.clinic_id is not None and hasattr(self.model, "clinic_id"):
            stmt = stmt.where(self.model.clinic_id == self.clinic_id)  # type: ignore[attr-defined]
        await self.session.execute(stmt)
