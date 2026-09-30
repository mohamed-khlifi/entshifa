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
