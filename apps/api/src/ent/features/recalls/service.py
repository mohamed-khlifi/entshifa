"""Manual recall use cases (P2-11)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.events.bus import get_event_bus
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.clinics.repository import ClinicRepository
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import Patient
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.features.recalls.constants import MUTABLE_STATUSES
from ent.features.recalls.dates import clinic_local_date, due_on_from_interval
from ent.features.recalls.events import recall_created_event
from ent.features.recalls.exceptions import (
    RecallDueRequiredError,
    RecallIdempotencyMismatchError,
    RecallInvalidStatusError,
    RecallNotFoundError,
    RecallVersionConflictError,
)
from ent.features.recalls.mapping import recall_snapshot, to_recall_read
from ent.features.recalls.models import Recall, RecallAction, RecallRequestIdempotency
from ent.features.recalls.repository import (
    RecallActionRepository,
    RecallIdempotencyRepository,
    RecallRepository,
)
from ent.features.recalls.schemas.requests import (
    RecallActionCreate,
    RecallAppointmentCreate,
    RecallBook,
    RecallBucket,
    RecallCancel,
    RecallComplete,
    RecallCreate,
    RecallUpdate,
)
from ent.features.recalls.schemas.responses import RecallRead, RecallSummaryRead
from ent.features.scheduling.schemas.requests import AppointmentCreate
from ent.features.scheduling.service import SchedulingService
from ent.features.users.repository import UserAdminRepository

_CONTACT = frozenset({"sms", "call", "email", "whatsapp"})


class RecallService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def create_recall(
        self,
        *,
        user: CurrentUser,
        body: RecallCreate,
        idempotency_key: str | None,
    ) -> RecallRead:
        self._bind(user)
        replay = await self._replay(user, idempotency_key, body)
        if replay is not None:
            return replay
        today = await self._today(user)
        patient = await self._patient(user, body.patient_id)
        due_on = _due_on(body, today)
        source_id = await self._source_encounter_id(
            user, patient_id=int(patient.id), public_id=body.source_encounter_id
        )
        assigned_id = await self._member_id(user, body.assigned_to_id)
        row = Recall(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            source_type="manual",
            source_id=source_id,
            reason_text=body.reason_text,
            reason_locale=body.reason_locale,
            due_on=due_on,
            window_days=body.window_days,
            action_type=body.action_type,
            action_config=_config(body),
            laterality=body.laterality,
            status="pending",
            assigned_to_id=assigned_id,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        repo = self._recalls(user)
        await repo.add(row)
        overlap_count = 0
        if body.appointment is not None:
            overlap_count = await self._attach_appointment(
                user, row, body.appointment, patient_public_id=patient.public_id
            )
        self._audit.record_write(
            action="create",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            after=recall_snapshot(row),
        )
        await self._store_idempotency(user, idempotency_key, body, row.public_id)
        await self._session.commit()
        loaded = await repo.get_for_read(row.public_id)
        if loaded is None:
            raise RecallNotFoundError(resource="recall")
        await get_event_bus().publish(
            recall_created_event(
                recall_public_id=loaded.public_id,
                patient_public_id=patient.public_id,
                clinic_id=user.clinic_id,
            )
        )
        self._audit.record_access(
            action="get",
            entity_type="recall",
            clinic_id=user.clinic_id,
            entity_id=loaded.id,
            entity_public_id=loaded.public_id,
            patient_id=loaded.patient_id,
        )
        await self._session.commit()
        sources = await self._sources(user, [loaded])
        return to_recall_read(
            loaded,
            today=today,
            source_encounter_id=sources.get(int(loaded.source_id or 0)),
            overlap_count=overlap_count,
        )

    async def list_recalls(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        bucket: RecallBucket | None,
        status: str | None,
        action_type: str | None,
        patient_public_id: str | None,
    ) -> PageSchema[RecallRead]:
        self._bind(user)
        today = await self._today(user)
        patient_id = None
        if patient_public_id is not None:
            patient_id = int((await self._patient(user, patient_public_id)).id)
        result = await self._recalls(user).list_recalls(
            today=today,
            bucket=bucket,
            status=status,
            action_type=action_type,
            patient_id=patient_id,
            page=page,
        )
        sources = await self._sources(user, result.items)
        self._audit.record_access(
            action="list",
            entity_type="recall",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return PageSchema(
            items=[
                to_recall_read(
                    row,
                    today=today,
                    source_encounter_id=sources.get(int(row.source_id or 0)),
                )
                for row in result.items
            ],
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def get_recall(self, *, user: CurrentUser, public_id: str) -> RecallRead:
        self._bind(user)
        today = await self._today(user)
        row = await self._require(user, public_id)
        sources = await self._sources(user, [row])
        self._audit.record_access(
            action="get",
            entity_type="recall",
            clinic_id=user.clinic_id,
            entity_id=row.id,
            entity_public_id=row.public_id,
            patient_id=row.patient_id,
        )
        await self._session.commit()
        return to_recall_read(
            row,
            today=today,
            source_encounter_id=sources.get(int(row.source_id or 0)),
        )

    async def get_summary(self, *, user: CurrentUser) -> RecallSummaryRead:
        self._bind(user)
        today = await self._today(user)
        overdue, upcoming, unreachable, active = await self._recalls(user).summary(
            today=today
        )
        self._audit.record_access(
            action="get_summary",
            entity_type="recall",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return RecallSummaryRead(
            overdue=overdue,
            upcoming=upcoming,
            unreachable=unreachable,
            active=active,
        )

    async def log_action(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: RecallActionCreate,
    ) -> RecallRead:
        self._bind(user)
        today = await self._today(user)
        row = await self._require_mutable(user, public_id, body.version)
        before = recall_snapshot(row)
        now = datetime.now(UTC).replace(tzinfo=None)
        await RecallActionRepository(self._session, user.clinic_id).add(
            RecallAction(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                recall_id=int(row.id),
                action=body.action,
                performed_at=now,
                performed_by_id=user.user_id,
                outcome=body.outcome,
                note=body.note,
                note_locale=body.note_locale if body.note else None,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
        if body.action in _CONTACT:
            row.attempts = int(row.attempts) + 1
            row.last_attempt_at = now
        if body.outcome == "unreachable":
            row.status = "unreachable"
        elif body.action == "booked":
            row.status = "booked"
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        self._audit.record_write(
            action="update",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=recall_snapshot(row),
        )
        await self._session.commit()
        return await self._read(user, row.public_id, today)

    async def book_appointment(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: RecallBook,
    ) -> RecallRead:
        self._bind(user)
        today = await self._today(user)
        row = await self._require_mutable(user, public_id, body.version)
        if row.appointment_id is not None:
            raise RecallInvalidStatusError(status="booked")
        patient = row.patient
        overlap_count = await self._attach_appointment(
            user,
            row,
            body.appointment,
            patient_public_id=patient.public_id,
        )
        row.version = int(row.version) + 1
        row.updated_by_id = user.user_id
        await self._session.commit()
        read = await self._read(user, row.public_id, today)
        read.overlap_count = overlap_count
        return read

    async def cancel_recall(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: RecallCancel,
    ) -> RecallRead:
        self._bind(user)
        today = await self._today(user)
        row = await self._require_mutable(user, public_id, body.version)
        before = recall_snapshot(row)
        row.status = "cancelled"
        row.cancelled_reason = body.reason
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        self._audit.record_write(
            action="cancel",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=recall_snapshot(row),
        )
        await self._session.commit()
        return await self._read(user, row.public_id, today)

    async def complete_recall(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: RecallComplete,
    ) -> RecallRead:
        self._bind(user)
        today = await self._today(user)
        row = await self._require_mutable(user, public_id, body.version)
        before = recall_snapshot(row)
        if body.completed_encounter_id is not None:
            row.completed_encounter_id = await self._source_encounter_id(
                user,
                patient_id=int(row.patient_id),
                public_id=body.completed_encounter_id,
            )
        row.status = "done"
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        self._audit.record_write(
            action="complete",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=recall_snapshot(row),
        )
        await self._session.commit()
        return await self._read(user, row.public_id, today)

    async def update_recall(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: RecallUpdate,
    ) -> RecallRead:
        self._bind(user)
        today = await self._today(user)
        row = await self._require_mutable(user, public_id, body.version)
        before = recall_snapshot(row)
        if body.due_on is not None:
            row.due_on = body.due_on
        if body.window_days is not None:
            row.window_days = body.window_days
        if body.reason_text is not None:
            row.reason_text = body.reason_text
            row.reason_locale = body.reason_locale or row.reason_locale
        if body.assigned_to_id is not None:
            row.assigned_to_id = await self._member_id(user, body.assigned_to_id)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        self._audit.record_write(
            action="update",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=recall_snapshot(row),
        )
        await self._session.commit()
        return await self._read(user, row.public_id, today)

    async def _attach_appointment(
        self,
        user: CurrentUser,
        row: Recall,
        appointment: RecallAppointmentCreate,
        *,
        patient_public_id: str,
    ) -> int:
        before = recall_snapshot(row)
        staged, overlaps = await SchedulingService(self._session).stage_appointment(
            user=user,
            body=AppointmentCreate(
                site_id=appointment.site_id,
                patient_id=patient_public_id,
                user_id=appointment.user_id,
                appointment_type_id=appointment.appointment_type_id,
                starts_at=appointment.starts_at,
                ends_at=appointment.ends_at,
                room=appointment.room,
                reason_text=row.reason_text,
            ),
            created_from_recall_id=int(row.id),
        )
        now = datetime.now(UTC).replace(tzinfo=None)
        await RecallActionRepository(self._session, user.clinic_id).add(
            RecallAction(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                recall_id=int(row.id),
                action="booked",
                performed_at=now,
                performed_by_id=user.user_id,
                outcome="confirmed",
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
        row.appointment_id = int(staged.id)
        row.status = "booked"
        row.updated_by_id = user.user_id
        self._audit.record_write(
            action="book",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=recall_snapshot(row),
        )
        return len(overlaps)

    async def _read(self, user: CurrentUser, public_id: str, today: date) -> RecallRead:
        row = await self._require(user, public_id)
        sources = await self._sources(user, [row])
        return to_recall_read(
            row,
            today=today,
            source_encounter_id=sources.get(int(row.source_id or 0)),
        )

    async def _require(self, user: CurrentUser, public_id: str) -> Recall:
        row = await self._recalls(user).get_for_read(public_id)
        if row is None:
            raise RecallNotFoundError(resource="recall", public_id=public_id)
        return row

    async def _require_mutable(
        self, user: CurrentUser, public_id: str, version: int
    ) -> Recall:
        row = await self._require(user, public_id)
        if row.version != version:
            raise RecallVersionConflictError(
                server_version=int(row.version),
                client_version=version,
            )
        if row.status not in MUTABLE_STATUSES:
            raise RecallInvalidStatusError(status=row.status)
        return row

    async def _patient(self, user: CurrentUser, public_id: str) -> Patient:
        patient = await PatientRepository(
            self._session, clinic_id=user.clinic_id
        ).get_visible(public_id, created_by_id=created_by_scope(user))
        if patient is None:
            raise NotFoundError(resource="patient", public_id=public_id)
        return patient

    async def _source_encounter_id(
        self,
        user: CurrentUser,
        *,
        patient_id: int,
        public_id: str | None,
    ) -> int | None:
        if public_id is None:
            return None
        encounter = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if encounter is None or int(encounter.patient_id) != patient_id:
            raise NotFoundError(resource="encounter", public_id=public_id)
        return int(encounter.id)

    async def _member_id(self, user: CurrentUser, public_id: str | None) -> int | None:
        if public_id is None:
            return None
        member = await UserAdminRepository(self._session).get_member(
            clinic_id=user.clinic_id,
            public_id=public_id,
        )
        if member is None:
            raise NotFoundError(resource="user", public_id=public_id)
        return int(member.id)

    async def _sources(self, user: CurrentUser, rows: list[Recall]) -> dict[int, str]:
        ids = {
            int(row.source_id)
            for row in rows
            if row.source_type == "manual" and row.source_id is not None
        }
        return await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).public_ids_for(ids)

    async def _today(self, user: CurrentUser) -> date:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic")
        try:
            return clinic_local_date(datetime.now(UTC), clinic.timezone)
        except ValueError as exc:
            raise ValidationError(reason="invalid_timezone") from exc

    async def _replay(
        self,
        user: CurrentUser,
        key: str | None,
        body: RecallCreate,
    ) -> RecallRead | None:
        if not key:
            return None
        existing = await RecallIdempotencyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_key(key)
        if existing is None:
            return None
        if existing.request_hash != _hash(body):
            raise RecallIdempotencyMismatchError()
        return await self.get_recall(user=user, public_id=existing.resource_public_id)

    async def _store_idempotency(
        self,
        user: CurrentUser,
        key: str | None,
        body: RecallCreate,
        resource_public_id: str,
    ) -> None:
        if not key:
            return
        await RecallIdempotencyRepository(self._session, clinic_id=user.clinic_id).add(
            RecallRequestIdempotency(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                idempotency_key=key,
                request_hash=_hash(body),
                resource_public_id=resource_public_id,
            )
        )

    def _recalls(self, user: CurrentUser) -> RecallRepository:
        return RecallRepository(self._session, clinic_id=user.clinic_id)

    def _bind(self, user: CurrentUser) -> None:
        set_user_id(user.user_id)
        set_clinic_id(user.clinic_id)


def _config(body: RecallCreate) -> dict[str, Any] | None:
    if body.action_config is None:
        return None
    dumped = body.action_config.model_dump(exclude_none=True)
    return dumped or None


def _due_on(body: RecallCreate, today: date) -> date:
    if body.due_on is not None:
        return body.due_on
    if body.interval_days is not None:
        return due_on_from_interval(today, body.interval_days)
    raise RecallDueRequiredError()


def _hash(body: RecallCreate) -> str:
    raw = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
