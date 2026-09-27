"""Scheduling HTTP endpoints (P1-07)."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Response, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.scheduling.dependencies import get_scheduling_service
from ent.features.scheduling.schemas.requests import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentTypeCreate,
    AppointmentTypeUpdate,
    AppointmentUpdate,
)
from ent.features.scheduling.schemas.responses import (
    AppointmentRead,
    AppointmentTypeRead,
    SchedulableDoctorRead,
    WaitingRoomEntryRead,
)
from ent.features.scheduling.service import SchedulingService

router = APIRouter(tags=["scheduling"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/scheduling/doctors",
    response_model=PageSchema[SchedulableDoctorRead],
)
async def list_schedulable_doctors(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_READ)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> PageSchema[SchedulableDoctorRead]:
    return await service.list_schedulable_doctors(user=user, page=_page(limit, offset))


@router.get("/api/v1/appointment-types", response_model=PageSchema[AppointmentTypeRead])
async def list_appointment_types(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_READ)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> PageSchema[AppointmentTypeRead]:
    return await service.list_appointment_types(user=user, page=_page(limit, offset))


@router.post(
    "/api/v1/appointment-types",
    response_model=AppointmentTypeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment_type(
    body: AppointmentTypeCreate,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_TYPE_MANAGE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentTypeRead:
    return await service.create_appointment_type(user=user, body=body)


@router.patch("/api/v1/appointment-types/{type_id}", response_model=AppointmentTypeRead)
async def update_appointment_type(
    type_id: str,
    body: AppointmentTypeUpdate,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_TYPE_MANAGE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentTypeRead:
    return await service.update_appointment_type(
        user=user,
        public_id=type_id,
        body=body,
    )


@router.delete(
    "/api/v1/appointment-types/{type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_appointment_type(
    type_id: str,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_TYPE_MANAGE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> Response:
    await service.delete_appointment_type(user=user, public_id=type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/v1/appointments", response_model=PageSchema[AppointmentRead])
async def list_appointments(
    starts_after: datetime = Query(..., alias="startsAfter"),
    starts_before: datetime = Query(..., alias="startsBefore"),
    doctor_user_id: str | None = Query(default=None, alias="doctorUserId"),
    room: str | None = Query(default=None, max_length=40),
    site_id: str | None = Query(default=None, alias="siteId"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_READ)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> PageSchema[AppointmentRead]:
    return await service.list_appointments(
        user=user,
        starts_after=starts_after,
        starts_before=starts_before,
        doctor_user_id=doctor_user_id,
        room=room,
        site_id=site_id,
        page=_page(limit, offset),
    )


@router.get(
    "/api/v1/appointments/waiting-room",
    response_model=PageSchema[WaitingRoomEntryRead],
)
async def list_waiting_room(
    on: date = Query(...),
    site_id: str | None = Query(default=None, alias="siteId"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_READ)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> PageSchema[WaitingRoomEntryRead]:
    return await service.list_waiting_room(
        user=user,
        on=on,
        site_id=site_id,
        page=_page(limit, offset),
    )


@router.post(
    "/api/v1/appointments",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    body: AppointmentCreate,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.create_appointment(user=user, body=body)


@router.get("/api/v1/appointments/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: str,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_READ)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.get_appointment(user=user, public_id=appointment_id)


@router.patch("/api/v1/appointments/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: str,
    body: AppointmentUpdate,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.update_appointment(
        user=user,
        public_id=appointment_id,
        body=body,
    )


@router.post(
    "/api/v1/appointments/{appointment_id}/arrive",
    response_model=AppointmentRead,
)
async def arrive_appointment(
    appointment_id: str,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.arrive(user=user, public_id=appointment_id)


@router.post(
    "/api/v1/appointments/{appointment_id}/in-room",
    response_model=AppointmentRead,
)
async def in_room_appointment(
    appointment_id: str,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.in_room(user=user, public_id=appointment_id)


@router.post(
    "/api/v1/appointments/{appointment_id}/complete",
    response_model=AppointmentRead,
)
async def complete_appointment(
    appointment_id: str,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.complete(user=user, public_id=appointment_id)


@router.post(
    "/api/v1/appointments/{appointment_id}/no-show",
    response_model=AppointmentRead,
)
async def no_show_appointment(
    appointment_id: str,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.mark_no_show(user=user, public_id=appointment_id)


@router.post(
    "/api/v1/appointments/{appointment_id}/cancel",
    response_model=AppointmentRead,
)
async def cancel_appointment(
    appointment_id: str,
    body: AppointmentCancel,
    user: CurrentUser = Depends(require(Permission.APPOINTMENT_WRITE)),
    service: SchedulingService = Depends(get_scheduling_service),
) -> AppointmentRead:
    return await service.cancel(user=user, public_id=appointment_id, body=body)
