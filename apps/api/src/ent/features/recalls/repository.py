"""Tenant-scoped recall queries. Every read goes through ``_base_query()``."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import Select, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import (
    Page,
    apply_pagination,
    normalize_pagination,
)
from ent.core.schemas.base import PaginationParams
from ent.core.utils.ids import new_ulid
from ent.features.recalls.constants import UPCOMING_HORIZON_DAYS
from ent.features.recalls.models import (
    Protocol,
    ProtocolRule,
    Recall,
    RecallAction,
    RecallRequestIdempotency,
)
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


class ProtocolRepository:
    """Scoped protocol queries with clinic-override precedence over system defaults."""

    def __init__(self, session: AsyncSession, clinic_id: int) -> None:
        self.session = session
        self.clinic_id = int(clinic_id)

    async def list_effective(
        self,
        *,
        trigger_type: str | None = None,
        active_only: bool = False,
    ) -> list[Protocol]:
        stmt = (
            select(Protocol)
            .where(
                Protocol.deleted_at.is_(None),
                or_(
                    Protocol.clinic_id.is_(None),
                    Protocol.clinic_id == self.clinic_id,
                ),
            )
            .options(selectinload(Protocol.rules))
            .order_by(Protocol.code.asc())
        )
        if trigger_type is not None:
            stmt = stmt.where(Protocol.trigger_type == trigger_type)
        rows = list((await self.session.scalars(stmt)).unique().all())
        effective_by_code: dict[str, Protocol] = {}
        for row in rows:
            current = effective_by_code.get(row.code)
            if current is None or row.clinic_id == self.clinic_id:
                effective_by_code[row.code] = row
        effective = [
            row
            for _, row in sorted(effective_by_code.items(), key=lambda item: item[0])
            if not active_only or row.is_active
        ]
        return effective

    async def get_effective_by_code(self, code: str) -> Protocol | None:
        stmt = (
            select(Protocol)
            .where(
                Protocol.deleted_at.is_(None),
                Protocol.code == code,
                or_(
                    Protocol.clinic_id.is_(None),
                    Protocol.clinic_id == self.clinic_id,
                ),
            )
            .options(selectinload(Protocol.rules))
        )
        rows = list((await self.session.scalars(stmt)).unique().all())
        if not rows:
            return None
        for row in rows:
            if row.clinic_id == self.clinic_id:
                return row
        return rows[0]

    async def get_rule_by_id(self, rule_id: int) -> ProtocolRule | None:
        result = await self.session.execute(
            select(ProtocolRule).where(
                ProtocolRule.id == rule_id,
                ProtocolRule.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_protocol_by_id(self, protocol_id: int) -> Protocol | None:
        result = await self.session.execute(
            select(Protocol).where(
                Protocol.id == protocol_id,
                Protocol.deleted_at.is_(None),
                or_(
                    Protocol.clinic_id.is_(None),
                    Protocol.clinic_id == self.clinic_id,
                ),
            )
        )
        return result.scalar_one_or_none()

    async def upsert_clinic_override(
        self,
        *,
        code: str,
        user_id: int,
        is_active: bool | None,
        rule_updates: list[tuple[int, int, int, dict[str, Any] | None]],
    ) -> Protocol | None:
        base = await self.get_effective_by_code(code)
        if base is None:
            return None

        if base.clinic_id == self.clinic_id:
            override = base
            if is_active is not None:
                override.is_active = is_active
            override.updated_by_id = user_id
            override.version = int(override.version) + 1
        else:
            override = Protocol(
                public_id=new_ulid(),
                clinic_id=self.clinic_id,
                code=base.code,
                name_key=base.name_key,
                trigger_type=base.trigger_type,
                trigger_concept_ids=list(base.trigger_concept_ids or []),
                is_active=base.is_active if is_active is None else is_active,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
            self.session.add(override)
            await self.session.flush()
            for base_rule in base.rules:
                if base_rule.deleted_at is not None:
                    continue
                self.session.add(
                    ProtocolRule(
                        public_id=new_ulid(),
                        protocol_id=int(override.id),
                        sequence=int(base_rule.sequence),
                        offset_days=int(base_rule.offset_days),
                        window_days=int(base_rule.window_days),
                        action_type=base_rule.action_type,
                        action_config=(
                            dict(base_rule.action_config)
                            if base_rule.action_config is not None
                            else None
                        ),
                        condition=(
                            dict(base_rule.condition)
                            if base_rule.condition is not None
                            else None
                        ),
                        label_key=base_rule.label_key,
                        created_by_id=user_id,
                        updated_by_id=user_id,
                    )
                )
            await self.session.flush()
            await self.session.refresh(override, attribute_names=["rules"])

        rules_by_seq = {
            int(rule.sequence): rule
            for rule in override.rules
            if rule.deleted_at is None
        }
        for seq, offset_days, window_days, action_config_patch in rule_updates:
            rule = rules_by_seq.get(seq)
            if rule is None:
                continue
            rule.offset_days = offset_days
            rule.window_days = window_days
            if action_config_patch is not None:
                merged = dict(rule.action_config or {})
                merged.update(action_config_patch)
                rule.action_config = merged
            rule.updated_by_id = user_id
            rule.version = int(rule.version) + 1

        await self.session.flush()
        return await self.get_effective_by_code(code)
