"""Tympanometry HTTP endpoints (P4-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.audiology.dependencies import (
    get_tympanometry_service,
    idempotency_key,
)
from ent.features.audiology.schemas.test_requests import (
    TympanometryCreate,
    TympanometryInterpret,
    TympanometryUpdate,
)
from ent.features.audiology.schemas.test_responses import TympanometryRead
from ent.features.audiology.tympanometry_service import TympanometryService
from ent.features.auth.dependencies import require

router = APIRouter(tags=["audiology"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/tympanograms",
    response_model=PageSchema[TympanometryRead],
)
async def list_tympanograms(
    patient_id: str | None = Query(default=None, min_length=26, max_length=26),
    encounter_id: str | None = Query(default=None, min_length=26, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: TympanometryService = Depends(get_tympanometry_service),
) -> PageSchema[TympanometryRead]:
    return await service.list_tympanograms(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
        encounter_public_id=encounter_id,
    )


@router.get(
    "/api/v1/patients/{patient_id}/tympanograms",
    response_model=PageSchema[TympanometryRead],
)
async def list_patient_tympanograms(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: TympanometryService = Depends(get_tympanometry_service),
) -> PageSchema[TympanometryRead]:
    return await service.list_tympanograms(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
    )


@router.post(
    "/api/v1/tympanograms",
    response_model=TympanometryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_tympanogram(
    body: TympanometryCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: TympanometryService = Depends(get_tympanometry_service),
    key: str | None = Depends(idempotency_key),
) -> TympanometryRead:
    return await service.create_tympanogram(
        user=user,
        body=body,
        idempotency_key=key,
    )


@router.get(
    "/api/v1/tympanograms/{tympanogram_id}",
    response_model=TympanometryRead,
)
async def get_tympanogram(
    tympanogram_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: TympanometryService = Depends(get_tympanometry_service),
) -> TympanometryRead:
    return await service.get_tympanogram(user=user, public_id=tympanogram_id)


@router.put(
    "/api/v1/tympanograms/{tympanogram_id}",
    response_model=TympanometryRead,
)
async def update_tympanogram(
    tympanogram_id: str,
    body: TympanometryUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: TympanometryService = Depends(get_tympanometry_service),
) -> TympanometryRead:
    return await service.update_tympanogram(
        user=user,
        public_id=tympanogram_id,
        body=body,
    )


@router.post(
    "/api/v1/tympanograms/{tympanogram_id}/interpret",
    response_model=TympanometryRead,
)
async def interpret_tympanogram(
    tympanogram_id: str,
    body: TympanometryInterpret,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_INTERPRET)),
    service: TympanometryService = Depends(get_tympanometry_service),
) -> TympanometryRead:
    return await service.interpret_tympanogram(
        user=user,
        public_id=tympanogram_id,
        body=body,
    )
