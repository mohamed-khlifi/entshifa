"""Encounter repositories. Signed visits cannot be rewritten here."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import (
    Page,
    apply_pagination,
    normalize_pagination,
)
from ent.core.schemas.base import PaginationParams
from ent.features.diagnoses.models import Diagnosis
from ent.features.encounters.exceptions import (
    EncounterInvalidTransitionError,
    EncounterLockedError,
)
from ent.features.encounters.models import (
    Encounter,
    EncounterAddendum,
    EncounterComplaint,
    EncounterSignature,
    EncounterTemplate,
)

_DETAIL = (
    selectinload(Encounter.complaints).selectinload(EncounterComplaint.concept),
    selectinload(Encounter.diagnoses).selectinload(Diagnosis.concept),
    selectinload(Encounter.diagnoses).selectinload(Diagnosis.promoted_problem),
    selectinload(Encounter.diagnoses).selectinload(Diagnosis.derived_from),
    selectinload(Encounter.addenda).selectinload(EncounterAddendum.author),
    selectinload(Encounter.signatures).selectinload(EncounterSignature.signer),
    selectinload(Encounter.patient),
    selectinload(Encounter.site),
    selectinload(Encounter.clinician),
    selectinload(Encounter.signed_by),
    selectinload(Encounter.appointment),
    selectinload(Encounter.template),
    selectinload(Encounter.previous_encounter),
)


class EncounterRepository(BaseRepository[Encounter]):
    model = Encounter

    def assert_draft(self, encounter: Encounter) -> None:
        """Reject any content write once the visit has left draft."""

        if encounter.status != "draft":
            raise EncounterLockedError(
                public_id=encounter.public_id,
                status=encounter.status,
            )

    def apply_draft_changes(
        self,
        encounter: Encounter,
        changes: dict[str, Any],
    ) -> None:
        self.assert_draft(encounter)
        for key, value in changes.items():
            setattr(encounter, key, value)

    def mark_signed(
        self,
        encounter: Encounter,
        *,
        locked_hash: str,
        signed_at: datetime,
        signed_by_id: int,
    ) -> None:
        self.assert_draft(encounter)
        encounter.status = "signed"
        encounter.locked_hash = locked_hash
        encounter.signed_at = signed_at
        encounter.signed_by_id = signed_by_id
        encounter.updated_by_id = signed_by_id
        encounter.version = int(encounter.version) + 1

    def mark_amended(self, encounter: Encounter, *, updated_by_id: int) -> None:
        if encounter.status not in {"signed", "amended"}:
            raise EncounterInvalidTransitionError(
                from_status=encounter.status,
                to_status="amended",
            )
        encounter.status = "amended"
        encounter.updated_by_id = updated_by_id
        encounter.version = int(encounter.version) + 1

    async def get_detail(self, public_id: str) -> Encounter | None:
        result = await self.session.execute(
            self._base_query().where(Encounter.public_id == public_id).options(*_DETAIL)
        )
        return result.scalar_one_or_none()

    async def list_for_patient(
        self,
        patient_id: int,
        page: PaginationParams | None,
    ) -> Page[Encounter]:
        resolved = normalize_pagination(page)
        filtered = self._base_query().where(Encounter.patient_id == patient_id)
        total = (
            await self.session.execute(
                select(func.count()).select_from(filtered.subquery())
            )
        ).scalar_one()
        stmt = filtered.options(*_DETAIL).order_by(
            Encounter.started_at.desc(), Encounter.id.desc()
        )
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

    async def replace_complaints(
        self,
        encounter: Encounter,
        rows: list[EncounterComplaint],
        *,
        deleted_by_id: int,
    ) -> None:
        self.assert_draft(encounter)
        complaints = EncounterComplaintRepository(self.session, self.clinic_id)
        existing = await complaints.list_for_encounter(int(encounter.id))
        deleted_at = datetime.now(UTC).replace(tzinfo=None)
        for row in existing:
            row.deleted_at = deleted_at
            row.deleted_by_id = deleted_by_id
            row.updated_by_id = deleted_by_id
        for row in rows:
            row.encounter_id = int(encounter.id)
            await complaints.add(row)


class EncounterComplaintRepository(BaseRepository[EncounterComplaint]):
    model = EncounterComplaint

    async def list_for_encounter(self, encounter_id: int) -> list[EncounterComplaint]:
        result = await self.session.scalars(
            self._base_query().where(EncounterComplaint.encounter_id == encounter_id)
        )
        return list(result.all())


class EncounterAddendumRepository(BaseRepository[EncounterAddendum]):
    model = EncounterAddendum


class EncounterSignatureRepository(BaseRepository[EncounterSignature]):
    model = EncounterSignature


class EncounterTemplateRepository(BaseRepository[EncounterTemplate]):
    """System templates have a null clinic_id, so visibility is not `_base_query`."""

    model = EncounterTemplate

    async def get_active_for_user(
        self,
        public_id: str,
        *,
        user_id: int,
    ) -> EncounterTemplate | None:
        if self.clinic_id is None:
            return None
        result = await self.session.execute(
            select(EncounterTemplate).where(
                EncounterTemplate.public_id == public_id,
                EncounterTemplate.deleted_at.is_(None),
                EncounterTemplate.is_active.is_(True),
                or_(
                    EncounterTemplate.clinic_id.is_(None),
                    EncounterTemplate.clinic_id == self.clinic_id,
                ),
                or_(
                    EncounterTemplate.user_id.is_(None),
                    EncounterTemplate.user_id == user_id,
                ),
            )
        )
        return result.scalar_one_or_none()

    async def get_effective_by_code(
        self,
        code: str,
        *,
        user_id: int,
    ) -> EncounterTemplate | None:
        """Resolve a template code following doctor > clinic > system precedence."""
        if self.clinic_id is None:
            return None
        # In MySQL, IS NULL evaluates to 1 when NULL, 0 when NOT NULL.
        # So user_id.is_(None) orders doctor override (0) before clinic/system (1).
        # clinic_id.is_(None) orders clinic override (0) before system (1).
        stmt = (
            select(EncounterTemplate)
            .where(
                EncounterTemplate.code == code,
                EncounterTemplate.deleted_at.is_(None),
                EncounterTemplate.is_active.is_(True),
                or_(
                    EncounterTemplate.clinic_id.is_(None),
                    EncounterTemplate.clinic_id == self.clinic_id,
                ),
                or_(
                    EncounterTemplate.user_id.is_(None),
                    EncounterTemplate.user_id == user_id,
                ),
            )
            .order_by(
                EncounterTemplate.user_id.is_(None),
                EncounterTemplate.clinic_id.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_effective_for_concept(
        self,
        concept_id: int,
        *,
        user_id: int,
    ) -> EncounterTemplate | None:
        """Find highest-priority active template whose trigger_concept_ids JSON contains concept_id."""
        if self.clinic_id is None:
            return None
        # Filter in Python / SQL candidate pool for active templates visible to user
        stmt = (
            select(EncounterTemplate)
            .where(
                EncounterTemplate.deleted_at.is_(None),
                EncounterTemplate.is_active.is_(True),
                or_(
                    EncounterTemplate.clinic_id.is_(None),
                    EncounterTemplate.clinic_id == self.clinic_id,
                ),
                or_(
                    EncounterTemplate.user_id.is_(None),
                    EncounterTemplate.user_id == user_id,
                ),
            )
            .order_by(
                EncounterTemplate.user_id.is_(None),
                EncounterTemplate.clinic_id.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        candidates = list(result.scalars().all())
        for candidate in candidates:
            triggers = candidate.trigger_concept_ids or []
            if concept_id in triggers or str(concept_id) in triggers:
                return candidate
        return None

    async def list_effective_for_user(
        self,
        *,
        user_id: int,
    ) -> list[EncounterTemplate]:
        """List distinct active templates visible to the user, with overrides taking precedence."""
        if self.clinic_id is None:
            return []
        stmt = (
            select(EncounterTemplate)
            .where(
                EncounterTemplate.deleted_at.is_(None),
                EncounterTemplate.is_active.is_(True),
                or_(
                    EncounterTemplate.clinic_id.is_(None),
                    EncounterTemplate.clinic_id == self.clinic_id,
                ),
                or_(
                    EncounterTemplate.user_id.is_(None),
                    EncounterTemplate.user_id == user_id,
                ),
            )
            .order_by(
                EncounterTemplate.code,
                EncounterTemplate.user_id.is_(None),
                EncounterTemplate.clinic_id.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        seen_codes: set[str] = set()
        effective: list[EncounterTemplate] = []
        for row in rows:
            if row.code not in seen_codes:
                seen_codes.add(row.code)
                effective.append(row)
        return effective

    async def get_exact_override(
        self,
        code: str,
        *,
        clinic_id: int,
        user_id: int | None,
    ) -> EncounterTemplate | None:
        """Find an exact override row for a clinic or doctor."""
        stmt = select(EncounterTemplate).where(
            EncounterTemplate.code == code,
            EncounterTemplate.clinic_id == clinic_id,
            EncounterTemplate.deleted_at.is_(None),
        )
        if user_id is None:
            stmt = stmt.where(EncounterTemplate.user_id.is_(None))
        else:
            stmt = stmt.where(EncounterTemplate.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
