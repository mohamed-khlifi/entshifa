"""Procedure HTTP endpoints (P3-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.procedures.dependencies import (
    get_content_locale,
    get_procedure_service,
)
from ent.features.procedures.schemas.requests import (
    ProcedureAddendumCreate,
    ProcedureRecordCreate,
    ProcedureRecordUpdate,
    ProcedureSign,
)
from ent.features.procedures.schemas.responses import ProcedureRecordRead
from ent.features.procedures.service import ProcedureRecordService

router = APIRouter(tags=["procedures"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/procedures",
    response_model=PageSchema[ProcedureRecordRead],
)
async def list_procedures(
    patient_id: str | None = Query(default=None, min_length=26, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[ProcedureRecordRead]:
    return await service.list_procedures(
        user=user,
        page=_page(limit, offset),
        content_locale=content_locale,
        patient_public_id=patient_id,
    )


@router.get(
    "/api/v1/patients/{patient_id}/procedures",
    response_model=PageSchema[ProcedureRecordRead],
)
async def list_patient_procedures(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[ProcedureRecordRead]:
    return await service.list_procedures(
        user=user,
        page=_page(limit, offset),
        content_locale=content_locale,
        patient_public_id=patient_id,
    )


@router.post(
    "/api/v1/procedures",
    response_model=ProcedureRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_procedure(
    body: ProcedureRecordCreate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> ProcedureRecordRead:
    return await service.create_procedure(
        user=user,
        body=body,
        content_locale=content_locale,
    )


@router.get("/api/v1/procedures/{procedure_id}", response_model=ProcedureRecordRead)
async def get_procedure(
    procedure_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> ProcedureRecordRead:
    return await service.get_procedure(
        user=user,
        public_id=procedure_id,
        content_locale=content_locale,
    )


@router.put("/api/v1/procedures/{procedure_id}", response_model=ProcedureRecordRead)
async def update_procedure(
    procedure_id: str,
    body: ProcedureRecordUpdate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> ProcedureRecordRead:
    return await service.update_procedure(
        user=user,
        public_id=procedure_id,
        body=body,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/procedures/{procedure_id}/sign",
    response_model=ProcedureRecordRead,
)
async def sign_procedure(
    procedure_id: str,
    body: ProcedureSign,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_SIGN)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> ProcedureRecordRead:
    return await service.sign_procedure(
        user=user,
        public_id=procedure_id,
        body=body,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/procedures/{procedure_id}/addenda",
    response_model=ProcedureRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_procedure_addendum(
    procedure_id: str,
    body: ProcedureAddendumCreate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_AMEND)),
    service: ProcedureRecordService = Depends(get_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> ProcedureRecordRead:
    return await service.add_addendum(
        user=user,
        public_id=procedure_id,
        body=body,
        content_locale=content_locale,
    )
