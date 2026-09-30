"""Tenant-scoped observation queries (architecture §25.6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.observations.models import (
    ExaminationSnapshot,
    Observation,
    ObservationComponent,
)


@dataclass(frozen=True, slots=True)
class ObservationDiffRow:
    """One body-site group with both visits filled in SQL."""

    body_site_concept_id: int | None
    map_region_code: str | None
    laterality: str
    concept_id: int
    public_id_a: str | None
    public_id_b: str | None
    status_a: str | None
    status_b: str | None
    ordinal_a: int | None
    ordinal_b: int | None
    numeric_a: Decimal | None
    numeric_b: Decimal | None
    text_a: str | None
    text_b: str | None
    value_concept_id_a: int | None
    value_concept_id_b: int | None


class ObservationRepository(BaseRepository[Observation]):
    model = Observation

    async def create_batch(
        self,
        rows: list[tuple[Observation, list[ObservationComponent]]],
    ) -> list[Observation]:
        stored: list[Observation] = []
        for observation, components in rows:
            await self.add(observation)
            for component in components:
                component.observation_id = int(observation.id)
                component.clinic_id = int(observation.clinic_id)
                self.session.add(component)
            stored.append(observation)
        if rows:
            await self.session.flush()
        return stored

    async def list_by_public_ids(self, public_ids: list[str]) -> list[Observation]:
        if not public_ids:
            return []
        rows = list(
            (
                await self.session.scalars(
                    self._base_query()
                    .where(Observation.public_id.in_(public_ids))
                    .options(selectinload(Observation.components))
                )
            ).all()
        )
        order = {public_id: index for index, public_id in enumerate(public_ids)}
        rows.sort(key=lambda row: order.get(str(row.public_id), 0))
        return rows

    async def list_by_encounter(
        self,
        encounter_public_id: str,
        *,
        page: PaginationParams | None,
    ) -> Page[Observation]:
        stmt = (
            self._base_query()
            .where(Observation.encounter_public_id == encounter_public_id)
            .options(selectinload(Observation.components))
            .order_by(
                Observation.body_site_concept_id,
                Observation.map_region_code,
                Observation.id,
            )
        )
        return await self._page(stmt, page)

    async def list_timeline(
        self,
        *,
        patient_id: int,
        concept_id: int,
        page: PaginationParams | None,
    ) -> Page[Observation]:
        stmt = (
            self._base_query()
            .where(
                Observation.patient_id == patient_id,
                Observation.concept_id == concept_id,
            )
            .options(selectinload(Observation.components))
            .order_by(Observation.effective_at.desc(), Observation.id.desc())
        )
        return await self._page(stmt, page)

    async def list_cohort(
        self,
        *,
        concept_id: int,
        ordinal_value: int,
        effective_from: datetime,
        effective_to: datetime,
        page: PaginationParams | None,
    ) -> Page[Observation]:
        # Matches ix_observation__cohort_ordinal
        # (clinic_id, concept_id, ordinal_value, effective_at).
        stmt = (
            self._base_query()
            .where(
                Observation.concept_id == concept_id,
                Observation.ordinal_value == ordinal_value,
                Observation.effective_at >= effective_from,
                Observation.effective_at < effective_to,
            )
            .order_by(Observation.effective_at.desc(), Observation.id.desc())
        )
        return await self._page(stmt, page)

    async def diff_encounters_by_body_site(
        self,
        *,
        patient_id: int,
        encounter_public_id_a: str,
        encounter_public_id_b: str,
    ) -> list[ObservationDiffRow]:
        """One grouped query. Visit values are aggregated in SQL, not in Python."""

        filtered = (
            self._base_query()
            .where(
                Observation.patient_id == patient_id,
                Observation.encounter_public_id.in_(
                    (encounter_public_id_a, encounter_public_id_b)
                ),
            )
            .subquery()
        )
        side_a = filtered.c.encounter_public_id == encounter_public_id_a
        side_b = filtered.c.encounter_public_id == encounter_public_id_b
        site_key = func.coalesce(filtered.c.body_site_concept_id, 0)
        region_key = func.coalesce(filtered.c.map_region_code, "")
        stmt = (
            select(
                func.max(filtered.c.body_site_concept_id).label("body_site_concept_id"),
                func.max(filtered.c.map_region_code).label("map_region_code"),
                filtered.c.laterality,
                filtered.c.concept_id,
                func.max(case((side_a, filtered.c.public_id), else_=None)).label(
                    "public_id_a"
                ),
                func.max(case((side_b, filtered.c.public_id), else_=None)).label(
                    "public_id_b"
                ),
                func.max(case((side_a, filtered.c.status), else_=None)).label(
                    "status_a"
                ),
                func.max(case((side_b, filtered.c.status), else_=None)).label(
                    "status_b"
                ),
                func.max(case((side_a, filtered.c.ordinal_value), else_=None)).label(
                    "ordinal_a"
                ),
                func.max(case((side_b, filtered.c.ordinal_value), else_=None)).label(
                    "ordinal_b"
                ),
                func.max(case((side_a, filtered.c.value_numeric), else_=None)).label(
                    "numeric_a"
                ),
                func.max(case((side_b, filtered.c.value_numeric), else_=None)).label(
                    "numeric_b"
                ),
                func.max(case((side_a, filtered.c.value_text), else_=None)).label(
                    "text_a"
                ),
                func.max(case((side_b, filtered.c.value_text), else_=None)).label(
                    "text_b"
                ),
                func.max(case((side_a, filtered.c.value_concept_id), else_=None)).label(
                    "value_concept_id_a"
                ),
                func.max(case((side_b, filtered.c.value_concept_id), else_=None)).label(
                    "value_concept_id_b"
                ),
            )
            .group_by(
                site_key, region_key, filtered.c.laterality, filtered.c.concept_id
            )
            .order_by(
                site_key, region_key, filtered.c.laterality, filtered.c.concept_id
            )
        )
        result = await self.session.execute(stmt)
        return [_diff_row(dict(row)) for row in result.mappings().all()]

    async def mark_deleted(self, row: Observation, by_user_id: int) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        row.deleted_at = now
        row.deleted_by_id = by_user_id
        row.updated_by_id = by_user_id
        for component in list(row.components):
            component.deleted_at = now
            component.deleted_by_id = by_user_id
            component.updated_by_id = by_user_id
        await self.session.flush()

    async def _page(
        self,
        stmt: Select[tuple[Observation]],
        page: PaginationParams | None,
    ) -> Page[Observation]:
        resolved = normalize_pagination(page)
        counted = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(counted)).scalar_one()
        limited = apply_pagination(stmt, resolved)
        rows = list((await self.session.scalars(limited)).all())
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=None,
        )


class ExaminationSnapshotRepository(BaseRepository[ExaminationSnapshot]):
    model = ExaminationSnapshot

    async def list_for_patient(
        self,
        patient_id: int,
        *,
        map_id: str | None,
        page: PaginationParams | None,
    ) -> Page[ExaminationSnapshot]:
        stmt = self._base_query().where(ExaminationSnapshot.patient_id == patient_id)
        if map_id is not None:
            stmt = stmt.where(ExaminationSnapshot.map_id == map_id)
        stmt = stmt.order_by(
            ExaminationSnapshot.created_at.desc(), ExaminationSnapshot.id.desc()
        )
        resolved = normalize_pagination(page)
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()
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


def _diff_row(row: dict[str, object]) -> ObservationDiffRow:
    return ObservationDiffRow(
        body_site_concept_id=_optional_int(row["body_site_concept_id"]),
        map_region_code=_optional_str(row["map_region_code"]),
        laterality=str(row["laterality"]),
        concept_id=_required_int(row["concept_id"]),
        public_id_a=_optional_str(row["public_id_a"]),
        public_id_b=_optional_str(row["public_id_b"]),
        status_a=_optional_str(row["status_a"]),
        status_b=_optional_str(row["status_b"]),
        ordinal_a=_optional_int(row["ordinal_a"]),
        ordinal_b=_optional_int(row["ordinal_b"]),
        numeric_a=_optional_decimal(row["numeric_a"]),
        numeric_b=_optional_decimal(row["numeric_b"]),
        text_a=_optional_str(row["text_a"]),
        text_b=_optional_str(row["text_b"]),
        value_concept_id_a=_optional_int(row["value_concept_id_a"]),
        value_concept_id_b=_optional_int(row["value_concept_id_b"]),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _required_int(value)


def _required_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | str | Decimal):
        msg = "expected an integer column"
        raise TypeError(msg)
    return int(value)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
