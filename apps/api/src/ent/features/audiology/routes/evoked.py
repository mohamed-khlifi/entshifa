"""OAE and ABR HTTP endpoints (P4-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.audiology.dependencies import (
    get_abr_result_service,
    get_oae_result_service,
    idempotency_key,
)
from ent.features.audiology.evoked_service import AbrResultService, OaeResultService
from ent.features.audiology.schemas.test_requests import (
    AbrInterpret,
    AbrResultCreate,
    AbrResultUpdate,
    OaeInterpret,
    OaeResultCreate,
    OaeResultUpdate,
)
from ent.features.audiology.schemas.test_responses import AbrResultRead, OaeResultRead
from ent.features.auth.dependencies import require

router = APIRouter(tags=["audiology"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/oae-results",
    response_model=PageSchema[OaeResultRead],
)
async def list_oae_results(
    patient_id: str | None = Query(default=None, min_length=26, max_length=26),
    encounter_id: str | None = Query(default=None, min_length=26, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: OaeResultService = Depends(get_oae_result_service),
) -> PageSchema[OaeResultRead]:
    return await service.list_oae_results(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
        encounter_public_id=encounter_id,
    )


@router.get(
    "/api/v1/patients/{patient_id}/oae-results",
    response_model=PageSchema[OaeResultRead],
)
async def list_patient_oae_results(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: OaeResultService = Depends(get_oae_result_service),
) -> PageSchema[OaeResultRead]:
    return await service.list_oae_results(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
    )


@router.post(
    "/api/v1/oae-results",
    response_model=OaeResultRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_oae_result(
    body: OaeResultCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: OaeResultService = Depends(get_oae_result_service),
    key: str | None = Depends(idempotency_key),
) -> OaeResultRead:
    return await service.create_oae_result(
        user=user,
        body=body,
        idempotency_key=key,
    )


@router.get(
    "/api/v1/oae-results/{oae_id}",
    response_model=OaeResultRead,
)
async def get_oae_result(
    oae_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: OaeResultService = Depends(get_oae_result_service),
) -> OaeResultRead:
    return await service.get_oae_result(user=user, public_id=oae_id)


@router.put(
    "/api/v1/oae-results/{oae_id}",
    response_model=OaeResultRead,
)
async def update_oae_result(
    oae_id: str,
    body: OaeResultUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: OaeResultService = Depends(get_oae_result_service),
) -> OaeResultRead:
    return await service.update_oae_result(
        user=user,
        public_id=oae_id,
        body=body,
    )


@router.post(
    "/api/v1/oae-results/{oae_id}/interpret",
    response_model=OaeResultRead,
)
async def interpret_oae_result(
    oae_id: str,
    body: OaeInterpret,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_INTERPRET)),
    service: OaeResultService = Depends(get_oae_result_service),
) -> OaeResultRead:
    return await service.interpret_oae_result(
        user=user,
        public_id=oae_id,
        body=body,
    )


@router.get(
    "/api/v1/abr-results",
    response_model=PageSchema[AbrResultRead],
)
async def list_abr_results(
    patient_id: str | None = Query(default=None, min_length=26, max_length=26),
    encounter_id: str | None = Query(default=None, min_length=26, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: AbrResultService = Depends(get_abr_result_service),
) -> PageSchema[AbrResultRead]:
    return await service.list_abr_results(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
        encounter_public_id=encounter_id,
    )


@router.get(
    "/api/v1/patients/{patient_id}/abr-results",
    response_model=PageSchema[AbrResultRead],
)
async def list_patient_abr_results(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: AbrResultService = Depends(get_abr_result_service),
) -> PageSchema[AbrResultRead]:
    return await service.list_abr_results(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
    )


@router.post(
    "/api/v1/abr-results",
    response_model=AbrResultRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_abr_result(
    body: AbrResultCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: AbrResultService = Depends(get_abr_result_service),
    key: str | None = Depends(idempotency_key),
) -> AbrResultRead:
    return await service.create_abr_result(
        user=user,
        body=body,
        idempotency_key=key,
    )


@router.get(
    "/api/v1/abr-results/{abr_id}",
    response_model=AbrResultRead,
)
async def get_abr_result(
    abr_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: AbrResultService = Depends(get_abr_result_service),
) -> AbrResultRead:
    return await service.get_abr_result(user=user, public_id=abr_id)


@router.put(
    "/api/v1/abr-results/{abr_id}",
    response_model=AbrResultRead,
)
async def update_abr_result(
    abr_id: str,
    body: AbrResultUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: AbrResultService = Depends(get_abr_result_service),
) -> AbrResultRead:
    return await service.update_abr_result(
        user=user,
        public_id=abr_id,
        body=body,
    )


@router.post(
    "/api/v1/abr-results/{abr_id}/interpret",
    response_model=AbrResultRead,
)
async def interpret_abr_result(
    abr_id: str,
    body: AbrInterpret,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_INTERPRET)),
    service: AbrResultService = Depends(get_abr_result_service),
) -> AbrResultRead:
    return await service.interpret_abr_result(
        user=user,
        public_id=abr_id,
        body=body,
    )
