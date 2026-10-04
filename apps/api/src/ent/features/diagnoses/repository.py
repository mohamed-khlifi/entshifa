"""Diagnosis queries. Signed visits are refused by the encounter guard."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.features.diagnoses.models import Diagnosis, UserDiagnosisFavorite


class DiagnosisRepository(BaseRepository[Diagnosis]):
    model = Diagnosis

    async def list_for_encounter(self, encounter_id: int) -> list[Diagnosis]:
        result = await self.session.scalars(
            self._base_query()
            .where(Diagnosis.encounter_id == encounter_id)
            .options(
                selectinload(Diagnosis.concept),
                selectinload(Diagnosis.promoted_problem),
                selectinload(Diagnosis.derived_from),
            )
            .order_by(Diagnosis.sort_order, Diagnosis.id)
        )
        return list(result.all())

    async def get_for_encounter(
        self, public_id: str, encounter_id: int
    ) -> Diagnosis | None:
        result = await self.session.scalars(
            self._base_query()
            .where(
                Diagnosis.public_id == public_id,
                Diagnosis.encounter_id == encounter_id,
            )
            .options(
                selectinload(Diagnosis.concept),
                selectinload(Diagnosis.promoted_problem),
                selectinload(Diagnosis.derived_from),
            )
        )
        return result.one_or_none()


class UserDiagnosisFavoriteRepository(BaseRepository[UserDiagnosisFavorite]):
    model = UserDiagnosisFavorite

    async def list_for_user(self, user_id: int) -> list[UserDiagnosisFavorite]:
        result = await self.session.scalars(
            self._base_query()
            .where(UserDiagnosisFavorite.user_id == user_id)
            .options(selectinload(UserDiagnosisFavorite.concept))
            .order_by(UserDiagnosisFavorite.sort_order, UserDiagnosisFavorite.id)
        )
        return list(result.all())

    async def list_for_user_including_deleted(
        self, user_id: int
    ) -> list[UserDiagnosisFavorite]:
        result = await self.session.scalars(
            self._including_deleted()
            .where(UserDiagnosisFavorite.user_id == user_id)
            .options(selectinload(UserDiagnosisFavorite.concept))
        )
        return list(result.all())

    def _including_deleted(self) -> Select[tuple[UserDiagnosisFavorite]]:
        stmt = select(UserDiagnosisFavorite)
        if self.clinic_id is not None:
            stmt = stmt.where(UserDiagnosisFavorite.clinic_id == self.clinic_id)
        return stmt
