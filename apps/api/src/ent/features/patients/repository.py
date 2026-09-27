"""Tenant-scoped patient queries. Every read goes through ``_base_query()``."""

from __future__ import annotations

from datetime import date
from typing import TypeVar

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import load_only

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import (
    Page,
    apply_pagination,
    apply_sort,
    next_cursor_from_rows,
    normalize_pagination,
)
from ent.core.schemas.base import PaginationParams
from ent.engines.patients.name_normalize import (
    fold_name_part,
    like_contains_pattern,
    normalize_phone,
)
from ent.features.attachments.repository import AttachmentRepository
from ent.features.patients.models import (
    Patient,
    PatientAllergy,
    PatientFlag,
    PatientHistory,
    PatientIdentifier,
    PatientMedication,
    PatientMergeLog,
    PatientProblem,
    PatientRequestIdempotency,
)
from ent.features.terminology.models import Concept
from ent.features.users.models import User

ChildT = TypeVar(
    "ChildT",
    PatientIdentifier,
    PatientAllergy,
    PatientMedication,
    PatientFlag,
    PatientProblem,
    PatientHistory,
)

_SUMMARY_COLUMNS = (
    Patient.id,
    Patient.public_id,
    Patient.mrn,
    Patient.first_name,
    Patient.last_name,
    Patient.first_name_alt,
    Patient.last_name_alt,
    Patient.birth_date,
    Patient.birth_date_is_estimated,
    Patient.sex,
    Patient.preferred_locale,
    Patient.phone_primary,
    Patient.version,
    Patient.created_by_id,
    Patient.created_at,
)


class PatientRepository(BaseRepository[Patient]):
    model = Patient

    async def get_visible(
        self,
        public_id: str,
        *,
        created_by_id: int | None,
    ) -> Patient | None:
        stmt = self._base_query().where(Patient.public_id == public_id)
        if created_by_id is not None:
            stmt = stmt.where(Patient.created_by_id == created_by_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        search: str | None,
        birth_date: date | None,
        sex: str | None,
        flag_code: str | None,
        created_by_id: int | None,
        sort: str | None,
        page: PaginationParams | None,
    ) -> Page[Patient]:
        resolved = normalize_pagination(page)
        stmt = self._base_query().options(load_only(*_SUMMARY_COLUMNS))
        if created_by_id is not None:
            stmt = stmt.where(Patient.created_by_id == created_by_id)
        if birth_date is not None:
            stmt = stmt.where(Patient.birth_date == birth_date)
        if sex is not None:
            stmt = stmt.where(Patient.sex == sex)
        if flag_code is not None:
            active_flags = (
                select(PatientFlag.patient_id)
                .where(
                    PatientFlag.clinic_id == self.clinic_id,
                    PatientFlag.deleted_at.is_(None),
                    PatientFlag.flag_code == flag_code,
                    PatientFlag.ended_on.is_(None),
                )
                .scalar_subquery()
            )
            stmt = stmt.where(Patient.id.in_(active_flags))
        if search and search.strip():
            stmt = stmt.where(or_(*_search_clauses(search.strip())))

        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.order_by(None).subquery())
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

    async def find_duplicate_candidates(
        self,
        *,
        name_normalized: str,
        birth_date: date,
        phones: tuple[str | None, ...],
    ) -> list[Patient]:
        clauses: list[ColumnElement[bool]] = [
            (Patient.name_normalized == name_normalized)
            & (Patient.birth_date == birth_date)
        ]
        present = [phone for phone in phones if phone]
        if present:
            clauses.append(Patient.phone_primary.in_(present))
            clauses.append(Patient.phone_secondary.in_(present))
        stmt = self._base_query().where(or_(*clauses)).limit(10)
        return list((await self.session.scalars(stmt)).all())

    async def allocate_mrn(self) -> str:
        """Next numeric MRN. Soft-deleted rows still occupy their number."""

        if self.clinic_id is None:
            msg = "MRN allocation requires a clinic"
            raise RuntimeError(msg)
        count = (
            await self.session.execute(
                select(func.count())
                .select_from(Patient)
                .where(Patient.clinic_id == self.clinic_id)
            )
        ).scalar_one()
        return f"{int(count or 0) + 1:06d}"

    async def concept_by_public_id(self, public_id: str) -> Concept | None:
        result = await self.session.execute(
            select(Concept).where(
                Concept.public_id == public_id,
                Concept.deleted_at.is_(None),
                Concept.is_active.is_(True),
                or_(
                    Concept.clinic_id.is_(None),
                    Concept.clinic_id == self.clinic_id,
                ),
            )
        )
        return result.scalar_one_or_none()

    async def concept_labels(
        self,
        concept_ids: set[int],
        *,
        locale: str,
        clinic_default_locale: str,
    ) -> dict[int, tuple[str, str, str | None]]:
        if not concept_ids:
            return {}
        from ent.features.terminology.repository import TerminologyRepository

        term = TerminologyRepository(self.session, self.clinic_id)
        concepts = (
            (
                await self.session.execute(
                    select(Concept).where(Concept.id.in_(concept_ids)),
                )
            )
            .scalars()
            .all()
        )
        by_id = {int(concept.id): concept for concept in concepts}
        translations = await term.load_translations_for_concepts(list(concept_ids))
        labels: dict[int, tuple[str, str, str | None]] = {}
        for concept_id in concept_ids:
            concept = by_id.get(concept_id)
            if concept is None:
                continue
            resolved = term.resolve_display(
                concept=concept,
                translations=translations.get(concept_id, []),
                locale=locale,
                clinic_default_locale=clinic_default_locale,
            )
            display = (
                resolved.patient_friendly or resolved.full_name or resolved.display
            )
            labels[concept_id] = (str(concept.public_id), str(concept.code), display)
        return labels

    async def user_public_ids(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = (
            await self.session.execute(
                select(User.id, User.public_id).where(User.id.in_(user_ids))
            )
        ).all()
        return {int(row.id): str(row.public_id) for row in rows}

    async def reassign_chart(
        self,
        *,
        from_patient_id: int,
        to_patient_id: int,
        actor_id: int,
    ) -> list[str]:
        moved: list[str] = []
        for child_type in (
            PatientIdentifierRepository,
            PatientAllergyRepository,
            PatientMedicationRepository,
            PatientFlagRepository,
            PatientProblemRepository,
            PatientHistoryRepository,
        ):
            repo = child_type(self.session, clinic_id=self.clinic_id)
            rows = await repo.list_for_patient(from_patient_id)
            for row in rows:
                row.patient_id = to_patient_id
                row.updated_by_id = actor_id
                moved.append(row.public_id)

        attachments = AttachmentRepository(self.session, clinic_id=self.clinic_id)
        for attachment in await attachments.list_for_patient(from_patient_id):
            attachment.patient_id = to_patient_id
            attachment.updated_by_id = actor_id
            moved.append(attachment.public_id)
        return moved


class PatientIdentifierRepository(BaseRepository[PatientIdentifier]):
    model = PatientIdentifier

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[PatientIdentifier]:
        return await _list_children(self, patient_id, limit=limit, offset=offset)


class PatientAllergyRepository(BaseRepository[PatientAllergy]):
    model = PatientAllergy

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[PatientAllergy]:
        return await _list_children(self, patient_id, limit=limit, offset=offset)


class PatientMedicationRepository(BaseRepository[PatientMedication]):
    model = PatientMedication

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[PatientMedication]:
        return await _list_children(self, patient_id, limit=limit, offset=offset)


class PatientFlagRepository(BaseRepository[PatientFlag]):
    model = PatientFlag

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[PatientFlag]:
        return await _list_children(self, patient_id, limit=limit, offset=offset)

    async def list_active(
        self,
        *,
        flag_code: str | None,
        patient_id: int | None,
        limit: int,
    ) -> list[PatientFlag]:
        stmt = self._base_query().where(PatientFlag.ended_on.is_(None))
        if flag_code is not None:
            stmt = stmt.where(PatientFlag.flag_code == flag_code)
        if patient_id is not None:
            stmt = stmt.where(PatientFlag.patient_id == patient_id)
        stmt = stmt.limit(limit)
        return list((await self.session.scalars(stmt)).all())


class PatientProblemRepository(BaseRepository[PatientProblem]):
    model = PatientProblem

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[PatientProblem]:
        return await _list_children(self, patient_id, limit=limit, offset=offset)


class PatientHistoryRepository(BaseRepository[PatientHistory]):
    model = PatientHistory

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[PatientHistory]:
        return await _list_children(self, patient_id, limit=limit, offset=offset)


class PatientMergeLogRepository(BaseRepository[PatientMergeLog]):
    model = PatientMergeLog


class PatientIdempotencyRepository(BaseRepository[PatientRequestIdempotency]):
    model = PatientRequestIdempotency

    async def get_by_key(self, key: str) -> PatientRequestIdempotency | None:
        result = await self.session.execute(
            self._base_query().where(PatientRequestIdempotency.idempotency_key == key)
        )
        return result.scalar_one_or_none()


def _search_clauses(search: str) -> list[ColumnElement[bool]]:
    clauses: list[ColumnElement[bool]] = [Patient.mrn == search]
    folded = fold_name_part(search)
    if folded:
        clauses.append(
            Patient.name_normalized.like(like_contains_pattern(folded), escape="\\")
        )
    phone = normalize_phone(search)
    if phone:
        clauses.append(Patient.phone_primary == phone)
        clauses.append(Patient.phone_secondary == phone)
    parsed = _parse_iso_date(search)
    if parsed is not None:
        clauses.append(Patient.birth_date == parsed)
    return clauses


def _parse_iso_date(value: str) -> date | None:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


async def _list_children(
    repo: BaseRepository[ChildT],
    patient_id: int,
    *,
    limit: int,
    offset: int = 0,
) -> list[ChildT]:
    patient_column = getattr(repo.model, "patient_id")
    stmt = (
        repo._base_query()
        .where(patient_column == patient_id)
        .offset(offset)
        .limit(limit)
    )
    return list((await repo.session.scalars(stmt)).all())


async def count_children(repo: BaseRepository[ChildT], patient_id: int) -> int:
    patient_column = getattr(repo.model, "patient_id")
    base = repo._base_query().where(patient_column == patient_id)
    total = (
        await repo.session.execute(
            select(func.count()).select_from(base.order_by(None).subquery())
        )
    ).scalar_one()
    return int(total or 0)
