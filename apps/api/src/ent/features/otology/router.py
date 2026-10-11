"""Otology HTTP endpoints (P3-06). Signing stays on the procedure record."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.otology.dependencies import get_content_locale, get_otology_service
from ent.features.otology.schemas.requests import (
    EarDeviceStatusUpdate,
    OtologyCreate,
    OtologyUpdate,
)
from ent.features.otology.schemas.responses import EarDeviceRead, OtologyExamRead
from ent.features.otology.service import OtologyService

router = APIRouter(tags=["otology"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.post(
    "/api/v1/otology-exams",
    response_model=OtologyExamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_otology_exam(
    body: OtologyCreate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: OtologyService = Depends(get_otology_service),
    content_locale: str = Depends(get_content_locale),
) -> OtologyExamRead:
    return await service.create_exam(
        user=user, body=body, content_locale=content_locale
    )


@router.get("/api/v1/otology-exams/{exam_id}", response_model=OtologyExamRead)
async def get_otology_exam(
    exam_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OtologyService = Depends(get_otology_service),
    content_locale: str = Depends(get_content_locale),
) -> OtologyExamRead:
    return await service.get_exam(
        user=user, public_id=exam_id, content_locale=content_locale
    )


@router.put("/api/v1/otology-exams/{exam_id}", response_model=OtologyExamRead)
async def update_otology_exam(
    exam_id: str,
    body: OtologyUpdate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: OtologyService = Depends(get_otology_service),
    content_locale: str = Depends(get_content_locale),
) -> OtologyExamRead:
    return await service.update_exam(
        user=user, public_id=exam_id, body=body, content_locale=content_locale
    )


@router.get(
    "/api/v1/patients/{patient_id}/otology-exams",
    response_model=PageSchema[OtologyExamRead],
)
async def list_patient_otology_exams(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OtologyService = Depends(get_otology_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[OtologyExamRead]:
    return await service.list_for_patient(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/procedures/{procedure_id}/otology-exam",
    response_model=OtologyExamRead,
)
async def get_procedure_otology_exam(
    procedure_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OtologyService = Depends(get_otology_service),
    content_locale: str = Depends(get_content_locale),
) -> OtologyExamRead:
    return await service.get_for_procedure(
        user=user,
        procedure_public_id=procedure_id,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/patients/{patient_id}/ear-devices",
    response_model=PageSchema[EarDeviceRead],
)
async def list_patient_ear_devices(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OtologyService = Depends(get_otology_service),
) -> PageSchema[EarDeviceRead]:
    return await service.list_devices(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
    )


@router.patch("/api/v1/ear-devices/{device_id}", response_model=EarDeviceRead)
async def update_ear_device_status(
    device_id: str,
    body: EarDeviceStatusUpdate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: OtologyService = Depends(get_otology_service),
) -> EarDeviceRead:
    return await service.update_device_status(user=user, public_id=device_id, body=body)
