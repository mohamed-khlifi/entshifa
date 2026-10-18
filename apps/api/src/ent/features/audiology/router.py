"""Audiogram HTTP endpoints (P4-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.audiology.dependencies import (
    get_audiology_service,
    idempotency_key,
)
from ent.features.audiology.schemas.requests import (
    AudiogramBaselineUpdate,
    AudiogramCreate,
    AudiogramFinalize,
    AudiogramInterpret,
    AudiogramUpdate,
)
from ent.features.audiology.schemas.responses import AudiogramRead
from ent.features.audiology.service import AudiologyService
from ent.features.auth.dependencies import require

router = APIRouter(tags=["audiology"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/audiograms",
    response_model=PageSchema[AudiogramRead],
)
async def list_audiograms(
    patient_id: str | None = Query(default=None, min_length=26, max_length=26),
    encounter_id: str | None = Query(default=None, min_length=26, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: AudiologyService = Depends(get_audiology_service),
) -> PageSchema[AudiogramRead]:
    return await service.list_audiograms(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
        encounter_public_id=encounter_id,
    )


@router.get(
    "/api/v1/patients/{patient_id}/audiograms",
    response_model=PageSchema[AudiogramRead],
)
async def list_patient_audiograms(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: AudiologyService = Depends(get_audiology_service),
) -> PageSchema[AudiogramRead]:
    return await service.list_audiograms(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
    )


@router.post(
    "/api/v1/audiograms",
    response_model=AudiogramRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_audiogram(
    body: AudiogramCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: AudiologyService = Depends(get_audiology_service),
    key: str | None = Depends(idempotency_key),
) -> AudiogramRead:
    return await service.create_audiogram(
        user=user,
        body=body,
        idempotency_key=key,
    )


@router.get("/api/v1/audiograms/{audiogram_id}", response_model=AudiogramRead)
async def get_audiogram(
    audiogram_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: AudiologyService = Depends(get_audiology_service),
) -> AudiogramRead:
    return await service.get_audiogram(user=user, public_id=audiogram_id)


@router.put("/api/v1/audiograms/{audiogram_id}", response_model=AudiogramRead)
async def update_audiogram(
    audiogram_id: str,
    body: AudiogramUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: AudiologyService = Depends(get_audiology_service),
) -> AudiogramRead:
    return await service.update_audiogram(
        user=user,
        public_id=audiogram_id,
        body=body,
    )


@router.post(
    "/api/v1/audiograms/{audiogram_id}/finalize",
    response_model=AudiogramRead,
)
async def finalize_audiogram(
    audiogram_id: str,
    body: AudiogramFinalize,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: AudiologyService = Depends(get_audiology_service),
) -> AudiogramRead:
    return await service.finalize_audiogram(
        user=user,
        public_id=audiogram_id,
        version=body.version,
    )


@router.post(
    "/api/v1/audiograms/{audiogram_id}/interpret",
    response_model=AudiogramRead,
)
async def interpret_audiogram(
    audiogram_id: str,
    body: AudiogramInterpret,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_INTERPRET)),
    service: AudiologyService = Depends(get_audiology_service),
) -> AudiogramRead:
    return await service.interpret_audiogram(
        user=user,
        public_id=audiogram_id,
        body=body,
    )


@router.post(
    "/api/v1/audiograms/{audiogram_id}/baseline",
    response_model=AudiogramRead,
)
async def update_audiogram_baseline(
    audiogram_id: str,
    body: AudiogramBaselineUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_INTERPRET)),
    service: AudiologyService = Depends(get_audiology_service),
) -> AudiogramRead:
    return await service.update_baseline(
        user=user,
        public_id=audiogram_id,
        body=body,
    )
