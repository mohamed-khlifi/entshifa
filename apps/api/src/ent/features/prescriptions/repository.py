"""Prescription queries. Clinical reads go through ``_base_query()``."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.prescriptions.models import (
    CalculationResultRow,
    Drug,
    DrugForm,
    FormularyEntry,
    Prescription,
    PrescriptionItem,
    PrescriptionRequestIdempotency,
    PrescriptionTemplate,
)

_DRUG_LOAD = selectinload(Drug.forms)
_FORMULARY_LOAD = (
    selectinload(FormularyEntry.drug_form)
    .selectinload(DrugForm.drug)
    .selectinload(Drug.concept)
)
_PRESCRIPTION_LOAD = (
    selectinload(Prescription.items)
    .selectinload(PrescriptionItem.drug_form)
    .selectinload(DrugForm.drug)
    .selectinload(Drug.concept)
)


class DrugRepository(BaseRepository[Drug]):
    model = Drug

    def _search_stmt(self, q: str | None) -> object:
        stmt = self._base_query()
        if q and q.strip():
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Drug.inn_name.ilike(like), Drug.code.ilike(like)))
        return stmt

    async def search(self, q: str | None, page: PaginationParams) -> Page[Drug]:
        resolved = normalize_pagination(page)
        filtered = self._search_stmt(q)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())  # type: ignore[attr-defined]
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(_DRUG_LOAD).order_by(Drug.inn_name, Drug.id),  # type: ignore[attr-defined]
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def get_by_ids(self, ids: set[int]) -> list[Drug]:
        if not ids:
            return []
        result = await self.session.scalars(self._base_query().where(Drug.id.in_(ids)))
        return list(result.all())


class DrugFormRepository(BaseRepository[DrugForm]):
    model = DrugForm

    async def get_loaded(self, public_id: str) -> DrugForm | None:
        result = await self.session.scalars(
            self._base_query()
            .where(DrugForm.public_id == public_id)
            .options(selectinload(DrugForm.drug))
        )
        return result.one_or_none()


class FormularyRepository(BaseRepository[FormularyEntry]):
    model = FormularyEntry

    def _filtered(self, q: str | None) -> object:
        stmt = self._base_query().where(FormularyEntry.is_available.is_(True))
        if q and q.strip():
            like = f"%{q.strip()}%"
            stmt = (
                stmt.join(FormularyEntry.drug_form)
                .join(DrugForm.drug)
                .where(
                    or_(
                        FormularyEntry.brand_name.ilike(like),
                        Drug.inn_name.ilike(like),
                        Drug.code.ilike(like),
                    )
                )
            )
        return stmt

    async def list_available(
        self, page: PaginationParams, *, q: str | None
    ) -> Page[FormularyEntry]:
        resolved = normalize_pagination(page)
        filtered = self._filtered(q)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())  # type: ignore[attr-defined]
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(_FORMULARY_LOAD).order_by(  # type: ignore[attr-defined]
                            FormularyEntry.brand_name,
                            FormularyEntry.id,
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )

    async def get_loaded(self, public_id: str) -> FormularyEntry | None:
        result = await self.session.scalars(
            self._base_query()
            .where(FormularyEntry.public_id == public_id)
            .options(_FORMULARY_LOAD)
        )
        return result.one_or_none()


class PrescriptionRepository(BaseRepository[Prescription]):
    model = Prescription

    async def get_loaded(self, public_id: str) -> Prescription | None:
        result = await self.session.scalars(
            self._base_query()
            .where(Prescription.public_id == public_id)
            .options(_PRESCRIPTION_LOAD)
        )
        return result.one_or_none()

    async def list_for_patient(
        self, patient_id: int, page: PaginationParams
    ) -> Page[Prescription]:
        resolved = normalize_pagination(page)
        filtered = self._base_query().where(Prescription.patient_id == patient_id)
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.options(_PRESCRIPTION_LOAD).order_by(
                            Prescription.issued_at.is_(None),
                            Prescription.issued_at.desc(),
                            Prescription.id.desc(),
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )


class PrescriptionTemplateRepository(BaseRepository[PrescriptionTemplate]):
    model = PrescriptionTemplate

    async def list_for_clinic(
        self, page: PaginationParams
    ) -> Page[PrescriptionTemplate]:
        resolved = normalize_pagination(page)
        filtered = self._base_query()
        total_value = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        rows = list(
            (
                await self.session.scalars(
                    apply_pagination(
                        filtered.order_by(
                            PrescriptionTemplate.code,
                            PrescriptionTemplate.id,
                        ),
                        resolved,
                    )
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total_value or 0),
            limit=resolved.limit,
            offset=resolved.offset,
        )


class CalculationResultRepository(BaseRepository[CalculationResultRow]):
    model = CalculationResultRow

    async def list_for_procedures(
        self,
        procedure_record_ids: list[int],
    ) -> list[CalculationResultRow]:
        if not procedure_record_ids:
            return []
        result = await self.session.scalars(
            self._base_query()
            .where(CalculationResultRow.procedure_record_id.in_(procedure_record_ids))
            .order_by(
                CalculationResultRow.computed_at.desc(),
                CalculationResultRow.id.desc(),
            )
        )
        return list(result.all())


class PrescriptionIdempotencyRepository(BaseRepository[PrescriptionRequestIdempotency]):
    model = PrescriptionRequestIdempotency

    async def get_by_key(self, key: str) -> PrescriptionRequestIdempotency | None:
        result = await self.session.scalars(
            self._base_query().where(
                PrescriptionRequestIdempotency.idempotency_key == key
            )
        )
        return result.one_or_none()
