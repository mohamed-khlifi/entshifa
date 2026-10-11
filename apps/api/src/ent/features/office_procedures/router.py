"""Short office-procedure HTTP endpoints (P3-07). Signing stays on the parent."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.office_procedures.dependencies import (
    get_content_locale,
    get_office_procedure_service,
)
from ent.features.office_procedures.schemas.requests import (
    OfficeProcedureCreate,
    OfficeProcedureUpdate,
)
from ent.features.office_procedures.schemas.responses import OfficeProcedureRead
from ent.features.office_procedures.service import OfficeProcedureService

router = APIRouter(tags=["office-procedures"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.post(
    "/api/v1/office-procedures",
    response_model=OfficeProcedureRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_office_procedure(
    body: OfficeProcedureCreate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: OfficeProcedureService = Depends(get_office_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> OfficeProcedureRead:
    return await service.create_procedure(
        user=user,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/office-procedures/{office_procedure_id}",
    response_model=OfficeProcedureRead,
)
async def get_office_procedure(
    office_procedure_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OfficeProcedureService = Depends(get_office_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> OfficeProcedureRead:
    return await service.get_procedure(
        user=user,
        public_id=office_procedure_id,
        content_locale=content_locale,
    )


@router.put(
    "/api/v1/office-procedures/{office_procedure_id}",
    response_model=OfficeProcedureRead,
)
async def update_office_procedure(
    office_procedure_id: str,
    body: OfficeProcedureUpdate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: OfficeProcedureService = Depends(get_office_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> OfficeProcedureRead:
    return await service.update_procedure(
        user=user,
        public_id=office_procedure_id,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/patients/{patient_id}/office-procedures",
    response_model=PageSchema[OfficeProcedureRead],
)
async def list_patient_office_procedures(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OfficeProcedureService = Depends(get_office_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[OfficeProcedureRead]:
    return await service.list_for_patient(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/procedures/{procedure_id}/office-procedure",
    response_model=OfficeProcedureRead,
)
async def get_procedure_office_procedure(
    procedure_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: OfficeProcedureService = Depends(get_office_procedure_service),
    content_locale: str = Depends(get_content_locale),
) -> OfficeProcedureRead:
    return await service.get_for_parent(
        user=user,
        procedure_public_id=procedure_id,
        content_locale=content_locale,
    )
