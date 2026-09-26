"""Resolve clinical settings: user → clinic → system (architecture §25.17)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError
from ent.features.clinics.repository import SettingRepository

SettingSource = Literal["user", "clinic", "system"]


@dataclass(frozen=True, slots=True)
class ResolvedSetting:
    key: str
    value: Any
    source: SettingSource


class SettingResolver:
    """Looks up scoped ``setting`` rows; never invents a clinical default."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SettingRepository(session)

    async def resolve(
        self,
        *,
        key: str,
        clinic_id: int,
        user_id: int,
    ) -> ResolvedSetting:
        user_row = await self._repo.get_scoped(
            key=key,
            clinic_id=clinic_id,
            user_id=user_id,
        )
        if user_row is not None:
            return ResolvedSetting(key=key, value=user_row.value, source="user")

        clinic_row = await self._repo.get_scoped(
            key=key,
            clinic_id=clinic_id,
            user_id=None,
        )
        if clinic_row is not None:
            return ResolvedSetting(key=key, value=clinic_row.value, source="clinic")

        system_row = await self._repo.get_scoped(
            key=key,
            clinic_id=None,
            user_id=None,
        )
        if system_row is not None:
            return ResolvedSetting(key=key, value=system_row.value, source="system")

        raise NotFoundError(resource="setting", key=key)

    async def resolve_many(
        self,
        *,
        keys: list[str],
        clinic_id: int,
        user_id: int,
    ) -> list[ResolvedSetting]:
        return [
            await self.resolve(key=key, clinic_id=clinic_id, user_id=user_id)
            for key in keys
        ]
