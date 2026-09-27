"""Scheduling use cases (P1-07)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ConflictError, NotFoundError
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.features.clinics.models import Clinic
from ent.features.clinics.repository import ClinicRepository, SiteRepository
from ent.features.patients.models import Patient
from ent.features.patients.repository import PatientRepository
from ent.features.scheduling.exceptions import (
    AppointmentInvalidTimeRangeError,
    AppointmentInvalidTransitionError,
)
from ent.features.scheduling.models import Appointment, AppointmentType
from ent.features.scheduling.repository import (
    AppointmentRepository,
    AppointmentTypeRepository,
)
from ent.features.scheduling.schemas.requests import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentTypeCreate,
    AppointmentTypeUpdate,
    AppointmentUpdate,
)
from ent.features.scheduling.schemas.responses import (
    AppointmentOverlapWarning,
    AppointmentRead,
    AppointmentTypeRead,
    QuestionnaireStatusRead,
    SchedulableDoctorRead,
    WaitingRoomEntryRead,
)
from ent.features.scheduling.transitions import can_transition
from ent.features.scheduling.utc import as_utc_aware, to_utc_naive
from ent.features.users.models import User
from ent.features.users.repository import UserAdminRepository


class SchedulingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def list_schedulable_doctors(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams | None,
    ) -> PageSchema[SchedulableDoctorRead]:
        self._bind(user)
        repo = UserAdminRepository(self._session)
        result = await repo.list_members(clinic_id=user.clinic_id, page=page)
        reads = [
            SchedulableDoctorRead(
                public_id=row.public_id,
                first_name=row.first_name,
                last_name=row.last_name,
            )
            for row in result.items
        ]
        self._audit.record_access(
            action="list",
            entity_type="user",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return PageSchema(
            items=reads,
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def list_appointment_types(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams | None,
    ) -> PageSchema[AppointmentTypeRead]:
        self._bind(user)
        repo = AppointmentTypeRepository(self._session, user.clinic_id)
        result = await repo.list(page=page, sort="code")
        self._audit.record_access(
            action="list",
            entity_type="appointment_type",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return _page(result, _appointment_type_read)

    async def create_appointment_type(
        self,
        *,
        user: CurrentUser,
        body: AppointmentTypeCreate,
    ) -> AppointmentTypeRead:
        self._bind(user)
        repo = AppointmentTypeRepository(self._session, user.clinic_id)
        existing = await repo.get_by_code(body.code)
        if existing is not None:
            raise ConflictError(field="code")
        row = AppointmentType(
            clinic_id=user.clinic_id,
            code=body.code,
            name_key=body.name_key,
            default_duration_min=body.default_duration_min,
            color=body.color,
            requires_room=body.requires_room,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await repo.add(row)
        self._audit.record_write(
            action="create",
            entity=row,
            clinic_id=user.clinic_id,
            after=_type_snapshot(row),
        )
        await self._session.commit()
        return _appointment_type_read(row)

    async def update_appointment_type(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AppointmentTypeUpdate,
    ) -> AppointmentTypeRead:
        self._bind(user)
        repo = AppointmentTypeRepository(self._session, user.clinic_id)
        row = await repo.get_by_public_id(public_id)
        if row is None:
            raise NotFoundError(resource="appointment_type")
        if row.version != body.version:
            raise ConflictError(field="version")
        before = _type_snapshot(row)
        if body.name_key is not None:
            row.name_key = body.name_key
        if body.default_duration_min is not None:
            row.default_duration_min = body.default_duration_min
        if body.color is not None:
            row.color = body.color
        if body.requires_room is not None:
            row.requires_room = body.requires_room
        row.updated_by_id = user.user_id
        row.version += 1
        self._audit.record_write(
            action="update",
            entity=row,
            clinic_id=user.clinic_id,
            before=before,
            after=_type_snapshot(row),
        )
        await self._session.commit()
        return _appointment_type_read(row)

    async def delete_appointment_type(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> None:
        self._bind(user)
        repo = AppointmentTypeRepository(self._session, user.clinic_id)
        row = await repo.get_by_public_id(public_id)
        if row is None:
            raise NotFoundError(resource="appointment_type")
        before = _type_snapshot(row)
        await repo.soft_delete(row.id, user.user_id)
        self._audit.record_write(
            action="delete",
            entity=row,
            clinic_id=user.clinic_id,
            before=before,
        )
        await self._session.commit()

    async def list_appointments(
        self,
        *,
        user: CurrentUser,
        starts_after: datetime,
        starts_before: datetime,
        doctor_user_id: str | None,
        room: str | None,
        site_id: str | None,
        page: PaginationParams | None,
    ) -> PageSchema[AppointmentRead]:
        self._bind(user)
        repo = AppointmentRepository(self._session, user.clinic_id)
        doctor_internal: int | None = None
        if doctor_user_id is not None:
            doctor_internal = await self._resolve_user_id(user, doctor_user_id)
        site_internal: int | None = None
        if site_id is not None:
            site_internal = await self._resolve_site_id(user, site_id)
        result = await repo.list_in_range(
            starts_after=to_utc_naive(starts_after),
            starts_before=to_utc_naive(starts_before),
            doctor_user_id=doctor_internal,
            room=room,
            site_id=site_internal,
            page=page,
        )
        self._audit.record_access(
            action="list",
            entity_type="appointment",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        reads = [await self._appointment_read(user, row) for row in result.items]
        return PageSchema(
            items=reads,
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def get_appointment(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AppointmentRead:
        self._bind(user)
        row = await self._require_appointment(user, public_id)
        self._audit.record_access(
            action="read",
            entity_type="appointment",
            entity_id=row.id,
            entity_public_id=row.public_id,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
        )
        await self._session.commit()
        return await self._appointment_read(user, row)

    async def create_appointment(
        self,
        *,
        user: CurrentUser,
        body: AppointmentCreate,
    ) -> AppointmentRead:
        self._bind(user)
        refs = await self._resolve_appointment_refs(user, body)
        starts = to_utc_naive(body.starts_at)
        ends = (
            to_utc_naive(body.ends_at)
            if body.ends_at is not None
            else starts + timedelta(minutes=refs.appointment_type.default_duration_min)
        )
        if ends <= starts:
            raise AppointmentInvalidTimeRangeError()
        overlaps = await AppointmentRepository(
            self._session, user.clinic_id
        ).find_overlaps(
            doctor_user_id=refs.doctor.id,
            starts_at=starts,
            ends_at=ends,
            exclude_appointment_id=None,
        )
        row = Appointment(
            clinic_id=user.clinic_id,
            site_id=refs.site.id,
            patient_id=refs.patient.id,
            user_id=refs.doctor.id,
            appointment_type_id=refs.appointment_type.id,
            starts_at=starts,
            ends_at=ends,
            status="scheduled",
            room=body.room,
            reason_text=body.reason_text,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        repo = AppointmentRepository(self._session, user.clinic_id)
        await repo.add(row)
        self._audit.record_write(
            action="create",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            after=_appointment_snapshot(row),
        )
        await self._session.commit()
        read = await self._appointment_read(user, row)
        read.overlap_warnings = _overlap_warnings(overlaps)
        return read

    async def update_appointment(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AppointmentUpdate,
    ) -> AppointmentRead:
        self._bind(user)
        row = await self._require_appointment(user, public_id)
        if row.version != body.version:
            raise ConflictError(field="version")
        if row.status in {"completed", "cancelled", "no_show"}:
            raise ConflictError(field="status")
        before = _appointment_snapshot(row)
        if body.site_id is not None:
            row.site_id = await self._resolve_site_id(user, body.site_id)
        if body.user_id is not None:
            row.user_id = await self._resolve_user_id(user, body.user_id)
        if body.appointment_type_id is not None:
            row.appointment_type_id = await self._resolve_type_id(
                user,
                body.appointment_type_id,
            )
        if body.starts_at is not None:
            row.starts_at = to_utc_naive(body.starts_at)
        if body.ends_at is not None:
            row.ends_at = to_utc_naive(body.ends_at)
        if body.room is not None:
            row.room = body.room
        if body.reason_text is not None:
            row.reason_text = body.reason_text
        if row.ends_at <= row.starts_at:
            raise AppointmentInvalidTimeRangeError()
        overlaps = await AppointmentRepository(
            self._session, user.clinic_id
        ).find_overlaps(
            doctor_user_id=row.user_id,
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            exclude_appointment_id=row.id,
        )
        row.updated_by_id = user.user_id
        row.version += 1
        self._audit.record_write(
            action="update",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=_appointment_snapshot(row),
        )
        await self._session.commit()
        read = await self._appointment_read(user, row)
        read.overlap_warnings = _overlap_warnings(overlaps)
        return read

    async def list_waiting_room(
        self,
        *,
        user: CurrentUser,
        on: date,
        site_id: str | None,
        page: PaginationParams | None,
    ) -> PageSchema[WaitingRoomEntryRead]:
        self._bind(user)
        clinic = await self._clinic(user)
        day_start, day_end = _clinic_day_bounds(on, clinic.timezone)
        site_internal: int | None = None
        if site_id is not None:
            site_internal = await self._resolve_site_id(user, site_id)
        repo = AppointmentRepository(self._session, user.clinic_id)
        result = await repo.list_waiting_room(
            site_id=site_internal,
            day_start=day_start,
            day_end=day_end,
            page=page,
        )
        self._audit.record_access(
            action="list",
            entity_type="waiting_room",
            clinic_id=user.clinic_id,
        )
        items: list[WaitingRoomEntryRead] = []
        for row in result.items:
            patient = await PatientRepository(self._session, user.clinic_id).get(
                row.patient_id,
            )
            doctor = await self._get_user_by_id(row.user_id)
            appt = await self._appointment_read(user, row)
            items.append(
                WaitingRoomEntryRead(
                    appointment=appt,
                    patient_display_name=_patient_name(patient),
                    doctor_display_name=_user_name(doctor),
                ),
            )
        await self._session.commit()
        return PageSchema(
            items=items,
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def arrive(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AppointmentRead:
        return await self._transition(user, public_id, "arrived", arrived_at=_now())

    async def in_room(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AppointmentRead:
        return await self._transition(user, public_id, "in_room", started_at=_now())

    async def complete(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AppointmentRead:
        return await self._transition(user, public_id, "completed", ended_at=_now())

    async def mark_no_show(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> AppointmentRead:
        return await self._transition(user, public_id, "no_show")

    async def cancel(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: AppointmentCancel,
    ) -> AppointmentRead:
        self._bind(user)
        row = await self._require_appointment(user, public_id)
        if not can_transition(row.status, "cancelled"):
            raise AppointmentInvalidTransitionError(
                from_status=row.status,
                to_status="cancelled",
            )
        before = _appointment_snapshot(row)
        row.status = "cancelled"
        row.cancellation_reason = body.cancellation_reason
        row.updated_by_id = user.user_id
        row.version += 1
        self._audit.record_write(
            action="cancel",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=_appointment_snapshot(row),
        )
        await self._session.commit()
        return await self._appointment_read(user, row)

    async def _transition(
        self,
        user: CurrentUser,
        public_id: str,
        to_status: str,
        *,
        arrived_at: datetime | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
    ) -> AppointmentRead:
        self._bind(user)
        row = await self._require_appointment(user, public_id)
        if not can_transition(row.status, to_status):
            raise AppointmentInvalidTransitionError(
                from_status=row.status,
                to_status=to_status,
            )
        before = _appointment_snapshot(row)
        row.status = to_status
        if arrived_at is not None:
            row.arrived_at = arrived_at
        if started_at is not None:
            row.started_at = started_at
        if ended_at is not None:
            row.ended_at = ended_at
        row.updated_by_id = user.user_id
        row.version += 1
        self._audit.record_write(
            action=to_status,
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=row.patient_id,
            before=before,
            after=_appointment_snapshot(row),
        )
        await self._session.commit()
        return await self._appointment_read(user, row)

    async def _appointment_read(
        self,
        user: CurrentUser,
        row: Appointment,
    ) -> AppointmentRead:
        site = await SiteRepository(self._session, user.clinic_id).get(row.site_id)
        patient = await PatientRepository(self._session, user.clinic_id).get(
            row.patient_id
        )
        doctor = await self._get_user_by_id(row.user_id)
        appt_type = await AppointmentTypeRepository(self._session, user.clinic_id).get(
            row.appointment_type_id,
        )
        if site is None or patient is None or doctor is None or appt_type is None:
            raise NotFoundError(resource="appointment")
        return AppointmentRead(
            public_id=row.public_id,
            site_id=site.public_id,
            patient_id=patient.public_id,
            user_id=doctor.public_id,
            appointment_type_id=appt_type.public_id,
            starts_at=as_utc_aware(row.starts_at),
            ends_at=as_utc_aware(row.ends_at),
            status=row.status,
            reason_text=row.reason_text,
            room=row.room,
            arrived_at=as_utc_aware(row.arrived_at) if row.arrived_at else None,
            started_at=as_utc_aware(row.started_at) if row.started_at else None,
            ended_at=as_utc_aware(row.ended_at) if row.ended_at else None,
            cancellation_reason=row.cancellation_reason,
            questionnaire_status=QuestionnaireStatusRead(status="not_applicable"),
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def _require_appointment(
        self,
        user: CurrentUser,
        public_id: str,
    ) -> Appointment:
        row = await AppointmentRepository(
            self._session, user.clinic_id
        ).get_by_public_id(
            public_id,
        )
        if row is None:
            raise NotFoundError(resource="appointment")
        return row

    async def _resolve_appointment_refs(
        self,
        user: CurrentUser,
        body: AppointmentCreate,
    ) -> Any:
        from dataclasses import dataclass

        @dataclass
        class Refs:
            site: Any
            patient: Patient
            doctor: User
            appointment_type: AppointmentType

        site_repo = SiteRepository(self._session, user.clinic_id)
        site = await site_repo.get_by_public_id(body.site_id)
        if site is None:
            raise NotFoundError(resource="site")
        patient = await PatientRepository(
            self._session, user.clinic_id
        ).get_by_public_id(
            body.patient_id,
        )
        if patient is None:
            raise NotFoundError(resource="patient")
        doctor = await UserAdminRepository(self._session).get_member(
            clinic_id=user.clinic_id,
            public_id=body.user_id,
        )
        if doctor is None:
            raise NotFoundError(resource="user")
        appt_type = await AppointmentTypeRepository(
            self._session,
            user.clinic_id,
        ).get_by_public_id(body.appointment_type_id)
        if appt_type is None:
            raise NotFoundError(resource="appointment_type")
        return Refs(
            site=site, patient=patient, doctor=doctor, appointment_type=appt_type
        )

    async def _resolve_site_id(self, user: CurrentUser, public_id: str) -> int:
        site = await SiteRepository(self._session, user.clinic_id).get_by_public_id(
            public_id,
        )
        if site is None:
            raise NotFoundError(resource="site")
        return site.id

    async def _resolve_user_id(self, user: CurrentUser, public_id: str) -> int:
        row = await UserAdminRepository(self._session).get_member(
            clinic_id=user.clinic_id,
            public_id=public_id,
        )
        if row is None:
            raise NotFoundError(resource="user")
        return row.id

    async def _get_user_by_id(self, user_id: int) -> User | None:
        from sqlalchemy import select

        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _resolve_type_id(self, user: CurrentUser, public_id: str) -> int:
        row = await AppointmentTypeRepository(
            self._session, user.clinic_id
        ).get_by_public_id(
            public_id,
        )
        if row is None:
            raise NotFoundError(resource="appointment_type")
        return row.id

    async def _clinic(self, user: CurrentUser) -> Clinic:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic")
        return clinic

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _clinic_day_bounds(on: date, timezone: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(timezone)
    start_local = datetime(on.year, on.month, on.day, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(UTC).replace(tzinfo=None),
        end_local.astimezone(UTC).replace(tzinfo=None),
    )


def _overlap_warnings(overlaps: list[Appointment]) -> list[AppointmentOverlapWarning]:
    if not overlaps:
        return []
    return [
        AppointmentOverlapWarning(
            overlapping_appointment_ids=[row.public_id for row in overlaps],
        ),
    ]


def _appointment_type_read(row: AppointmentType) -> AppointmentTypeRead:
    return AppointmentTypeRead(
        public_id=row.public_id,
        code=row.code,
        name_key=row.name_key,
        default_duration_min=row.default_duration_min,
        color=row.color,
        requires_room=row.requires_room,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _type_snapshot(row: AppointmentType) -> dict[str, Any]:
    return {
        "code": row.code,
        "nameKey": row.name_key,
        "defaultDurationMin": row.default_duration_min,
    }


def _appointment_snapshot(row: Appointment) -> dict[str, Any]:
    return {
        "status": row.status,
        "startsAt": row.starts_at.isoformat(),
        "endsAt": row.ends_at.isoformat(),
    }


def _patient_name(patient: Patient | None) -> str:
    if patient is None:
        return ""
    return f"{patient.first_name} {patient.last_name}".strip()


def _user_name(user: User | None) -> str:
    if user is None:
        return ""
    return f"{user.first_name} {user.last_name}".strip()


def _page(result: Any, mapper: Any) -> PageSchema[Any]:
    return PageSchema(
        items=[mapper(row) for row in result.items],
        page=PageMeta(
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            next_cursor=result.next_cursor,
        ),
    )
