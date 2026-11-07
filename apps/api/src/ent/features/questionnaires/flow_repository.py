"""Tenant-scoped questionnaire invitation and response queries (P5-03)."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.questionnaires.models import (
    QuestionnaireInvitation,
    QuestionnaireRequestIdempotency,
    QuestionnaireResponse,
)


class QuestionnaireInvitationRepository(BaseRepository[QuestionnaireInvitation]):
    model = QuestionnaireInvitation

    async def list_for_patient(
        self,
        *,
        patient_id: int,
        page: PaginationParams | None,
    ) -> Page[QuestionnaireInvitation]:
        resolved = normalize_pagination(page)
        stmt = (
            self._base_query()
            .where(QuestionnaireInvitation.patient_id == patient_id)
            .order_by(QuestionnaireInvitation.sent_at.desc())
        )
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(await self.session.scalar(total_stmt) or 0)
        rows = list(
            await self.session.scalars(
                stmt.limit(resolved.limit).offset(resolved.offset),
            ),
        )
        return Page(
            items=rows,
            total=total,
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def has_active_uncompleted(
        self,
        *,
        patient_id: int,
        now: datetime,
    ) -> bool:
        stmt = (
            self._base_query()
            .where(
                QuestionnaireInvitation.patient_id == patient_id,
                QuestionnaireInvitation.completed_at.is_(None),
                QuestionnaireInvitation.expires_at > now,
            )
            .limit(1)
        )
        row = await self.session.scalar(stmt)
        return row is not None


class QuestionnaireInvitationGlobalRepository:
    """Token lookup without clinic scope (hash is globally unique)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> QuestionnaireInvitation | None:
        stmt = select(QuestionnaireInvitation).where(
            QuestionnaireInvitation.deleted_at.is_(None),
            QuestionnaireInvitation.token_hash == token_hash,
        )
        return cast(
            QuestionnaireInvitation | None,
            await self.session.scalar(stmt),
        )


class QuestionnaireResponseRepository(BaseRepository[QuestionnaireResponse]):
    model = QuestionnaireResponse

    _DETAIL_LOAD = (selectinload(QuestionnaireResponse.answers),)

    async def list_for_patient(
        self,
        *,
        patient_id: int,
        instrument_version_id: int | None,
        encounter_id: int | None,
        page: PaginationParams | None,
    ) -> Page[QuestionnaireResponse]:
        resolved = normalize_pagination(page)
        stmt = (
            self._base_query()
            .where(QuestionnaireResponse.patient_id == patient_id)
            .options(*self._DETAIL_LOAD)
            .order_by(QuestionnaireResponse.completed_at.desc())
        )
        if instrument_version_id is not None:
            stmt = stmt.where(
                QuestionnaireResponse.instrument_version_id == instrument_version_id,
            )
        if encounter_id is not None:
            stmt = stmt.where(QuestionnaireResponse.encounter_id == encounter_id)
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(await self.session.scalar(total_stmt) or 0)
        rows = list(
            await self.session.scalars(
                stmt.limit(resolved.limit).offset(resolved.offset)
            )
        )
        return Page(
            items=rows,
            total=total,
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def get_detail(self, public_id: str) -> QuestionnaireResponse | None:
        stmt = (
            self._base_query()
            .where(QuestionnaireResponse.public_id == public_id)
            .options(*self._DETAIL_LOAD)
        )
        return cast(QuestionnaireResponse | None, await self.session.scalar(stmt))

    async def latest_for_patient_version(
        self,
        *,
        patient_id: int,
        instrument_version_id: int,
        exclude_id: int | None = None,
    ) -> QuestionnaireResponse | None:
        stmt = (
            self._base_query()
            .where(
                QuestionnaireResponse.patient_id == patient_id,
                QuestionnaireResponse.instrument_version_id == instrument_version_id,
            )
            .order_by(QuestionnaireResponse.completed_at.desc())
            .limit(1)
        )
        if exclude_id is not None:
            stmt = stmt.where(QuestionnaireResponse.id != exclude_id)
        return cast(QuestionnaireResponse | None, await self.session.scalar(stmt))

    async def completed_between(
        self,
        *,
        patient_id: int,
        start: datetime,
        end: datetime,
    ) -> bool:
        stmt = (
            self._base_query()
            .where(
                QuestionnaireResponse.patient_id == patient_id,
                QuestionnaireResponse.completed_at >= start,
                QuestionnaireResponse.completed_at < end,
            )
            .limit(1)
        )
        return (await self.session.scalar(stmt)) is not None


class QuestionnaireIdempotencyRepository(
    BaseRepository[QuestionnaireRequestIdempotency]
):
    model = QuestionnaireRequestIdempotency

    async def get_by_key(self, key: str) -> QuestionnaireRequestIdempotency | None:
        result = await self.session.execute(
            self._base_query().where(
                QuestionnaireRequestIdempotency.idempotency_key == key,
            ),
        )
        return result.scalar_one_or_none()
