"""Clinic feature repositories."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.repository.base import BaseRepository
from ent.core.repository.filters import Eq, FilterSet, SearchOn
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic, Setting, Site


class SiteFilter(FilterSet):
    search: str | None = SearchOn("name", "city", normalize=True)
    is_primary: bool | None = Eq("is_primary")
    city: str | None = Eq("city")


class SiteRepository(BaseRepository[Site]):
    model = Site

    async def clear_primary_except(self, *, keep_id: int | None) -> None:
        """Unset is_primary on all sites in this clinic except ``keep_id``."""

        stmt = (
            update(Site)
            .where(
                Site.clinic_id == self.clinic_id,
                Site.deleted_at.is_(None),
                Site.is_primary.is_(True),
            )
            .values(is_primary=False)
        )
        if keep_id is not None:
            stmt = stmt.where(Site.id != keep_id)
        await self.session.execute(stmt)

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self._base_query().subquery()),
        )
        return int(result.scalar_one() or 0)


class ClinicRepository:
    """Clinic is a global (non-tenant) table; queries are not clinic_id-scoped."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_query(self) -> Select[tuple[Clinic]]:
        return select(Clinic).where(Clinic.deleted_at.is_(None))

    async def get(self, id_: int) -> Clinic | None:
        result = await self.session.execute(self._base_query().where(Clinic.id == id_))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: str) -> Clinic | None:
        result = await self.session.execute(
            self._base_query().where(Clinic.public_id == public_id),
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Clinic | None:
        result = await self.session.execute(
            self._base_query().where(Clinic.slug == slug)
        )
        return result.scalar_one_or_none()

    async def add(self, clinic: Clinic) -> Clinic:
        self.session.add(clinic)
        await self.session.flush()
        return clinic


class SettingRepository:
    """Scoped setting rows; system defaults have NULL clinic_id and user_id."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_query(self) -> Select[tuple[Setting]]:
        return select(Setting).where(Setting.deleted_at.is_(None))

    async def get_scoped(
        self,
        *,
        key: str,
        clinic_id: int | None,
        user_id: int | None,
    ) -> Setting | None:
        stmt = self._base_query().where(Setting.key == key)
        if clinic_id is None:
            stmt = stmt.where(Setting.clinic_id.is_(None))
        else:
            stmt = stmt.where(Setting.clinic_id == clinic_id)
        if user_id is None:
            stmt = stmt.where(Setting.user_id.is_(None))
        else:
            stmt = stmt.where(Setting.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_scoped(
        self,
        *,
        key: str,
        value: Any,
        clinic_id: int | None,
        user_id: int | None,
        by_user_id: int,
    ) -> Setting:
        existing = await self.get_scoped(
            key=key,
            clinic_id=clinic_id,
            user_id=user_id,
        )
        if existing is not None:
            existing.value = value
            existing.updated_by_id = by_user_id
            await self.session.flush()
            return existing

        row = Setting(
            public_id=new_ulid(),
            clinic_id=clinic_id,
            user_id=user_id,
            key=key,
            value=value,
            created_by_id=by_user_id,
            updated_by_id=by_user_id,
        )
        self.session.add(row)
        await self.session.flush()
        return row
