"""Endoscopy HTTP endpoints (P3-02). Signing stays on the procedure record."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.endoscopy.dependencies import (
    get_content_locale,
    get_endoscopy_service,
)
from ent.features.endoscopy.schemas.requests import EndoscopyCreate, EndoscopyUpdate
from ent.features.endoscopy.schemas.responses import EndoscopyExamRead
from ent.features.endoscopy.service import EndoscopyService

router = APIRouter(tags=["endoscopy"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.post(
    "/api/v1/endoscopies",
    response_model=EndoscopyExamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_endoscopy(
    body: EndoscopyCreate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: EndoscopyService = Depends(get_endoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> EndoscopyExamRead:
    return await service.create_exam(
        user=user,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/endoscopies/{endoscopy_id}",
    response_model=EndoscopyExamRead,
)
async def get_endoscopy(
    endoscopy_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: EndoscopyService = Depends(get_endoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> EndoscopyExamRead:
    return await service.get_exam(
        user=user,
        public_id=endoscopy_id,
        content_locale=content_locale,
    )


@router.put(
    "/api/v1/endoscopies/{endoscopy_id}",
    response_model=EndoscopyExamRead,
)
async def update_endoscopy(
    endoscopy_id: str,
    body: EndoscopyUpdate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: EndoscopyService = Depends(get_endoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> EndoscopyExamRead:
    return await service.update_exam(
        user=user,
        public_id=endoscopy_id,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/patients/{patient_id}/endoscopies",
    response_model=PageSchema[EndoscopyExamRead],
)
async def list_patient_endoscopies(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: EndoscopyService = Depends(get_endoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[EndoscopyExamRead]:
    return await service.list_for_patient(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/procedures/{procedure_id}/endoscopy",
    response_model=EndoscopyExamRead,
)
async def get_procedure_endoscopy(
    procedure_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: EndoscopyService = Depends(get_endoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> EndoscopyExamRead:
    return await service.get_for_procedure(
        user=user,
        procedure_public_id=procedure_id,
        content_locale=content_locale,
    )
