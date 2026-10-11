"""Laryngoscopy HTTP endpoints (P3-04). Signing stays on the procedure record."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.laryngoscopy.dependencies import (
    get_content_locale,
    get_laryngoscopy_service,
)
from ent.features.laryngoscopy.schemas.requests import (
    LaryngoscopyCreate,
    LaryngoscopyUpdate,
)
from ent.features.laryngoscopy.schemas.responses import LaryngoscopyExamRead
from ent.features.laryngoscopy.service import LaryngoscopyService

router = APIRouter(tags=["laryngoscopy"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.post(
    "/api/v1/laryngoscopies",
    response_model=LaryngoscopyExamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_laryngoscopy(
    body: LaryngoscopyCreate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: LaryngoscopyService = Depends(get_laryngoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> LaryngoscopyExamRead:
    return await service.create_exam(
        user=user,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/laryngoscopies/{laryngoscopy_id}",
    response_model=LaryngoscopyExamRead,
)
async def get_laryngoscopy(
    laryngoscopy_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: LaryngoscopyService = Depends(get_laryngoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> LaryngoscopyExamRead:
    return await service.get_exam(
        user=user,
        public_id=laryngoscopy_id,
        content_locale=content_locale,
    )


@router.put(
    "/api/v1/laryngoscopies/{laryngoscopy_id}",
    response_model=LaryngoscopyExamRead,
)
async def update_laryngoscopy(
    laryngoscopy_id: str,
    body: LaryngoscopyUpdate,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_WRITE)),
    service: LaryngoscopyService = Depends(get_laryngoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> LaryngoscopyExamRead:
    return await service.update_exam(
        user=user,
        public_id=laryngoscopy_id,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/patients/{patient_id}/laryngoscopies",
    response_model=PageSchema[LaryngoscopyExamRead],
)
async def list_patient_laryngoscopies(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: LaryngoscopyService = Depends(get_laryngoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[LaryngoscopyExamRead]:
    return await service.list_for_patient(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/procedures/{procedure_id}/laryngoscopy",
    response_model=LaryngoscopyExamRead,
)
async def get_procedure_laryngoscopy(
    procedure_id: str,
    user: CurrentUser = Depends(require(Permission.PROCEDURE_READ)),
    service: LaryngoscopyService = Depends(get_laryngoscopy_service),
    content_locale: str = Depends(get_content_locale),
) -> LaryngoscopyExamRead:
    return await service.get_for_procedure(
        user=user,
        procedure_public_id=procedure_id,
        content_locale=content_locale,
    )
