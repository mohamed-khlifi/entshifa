"""Observation HTTP endpoints (P2-01)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.observations.dependencies import (
    get_content_locale,
    get_observation_service,
)
from ent.features.observations.schemas.requests import (
    ExaminationSnapshotCreate,
    ObservationBatchCreate,
    ObservationUpdate,
)
from ent.features.observations.schemas.responses import (
    ExaminationSnapshotRead,
    ObservationDiffRead,
    ObservationRead,
)
from ent.features.observations.service import ObservationService

router = APIRouter(prefix="/api/v1/observations", tags=["observations"])


@router.post(
    "/patient/{patient_id}/batch",
    response_model=list[ObservationRead],
    status_code=status.HTTP_201_CREATED,
)
async def record_observations(
    patient_id: str,
    body: ObservationBatchCreate,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: ObservationService = Depends(get_observation_service),
    content_locale: str = Depends(get_content_locale),
) -> list[ObservationRead]:
    return await service.record_batch(
        user=user,
        patient_public_id=patient_id,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/patient/{patient_id}/diff",
    response_model=list[ObservationDiffRead],
)
async def diff_observations(
    patient_id: str,
    encounter_a: str | None = Query(
        default=None, alias="encounterA", min_length=26, max_length=26
    ),
    encounter_b: str | None = Query(
        default=None, alias="encounterB", min_length=26, max_length=26
    ),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: ObservationService = Depends(get_observation_service),
    content_locale: str = Depends(get_content_locale),
) -> list[ObservationDiffRead]:
    return await service.get_encounter_diff(
        user=user,
        patient_public_id=patient_id,
        encounter_public_id_a=encounter_a,
        encounter_public_id_b=encounter_b,
        content_locale=content_locale,
    )


@router.get(
    "/patient/{patient_id}/concept/{code}/timeline",
    response_model=PageSchema[ObservationRead],
)
async def observation_timeline(
    patient_id: str,
    code: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: ObservationService = Depends(get_observation_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[ObservationRead]:
    return await service.list_timeline(
        user=user,
        patient_public_id=patient_id,
        concept_code=code,
        page=PaginationParams(limit=limit, offset=offset),
        content_locale=content_locale,
    )


@router.post(
    "/patient/{patient_id}/snapshots",
    response_model=ExaminationSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_snapshot(
    patient_id: str,
    body: ExaminationSnapshotCreate,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: ObservationService = Depends(get_observation_service),
) -> ExaminationSnapshotRead:
    return await service.record_snapshot(
        user=user,
        patient_public_id=patient_id,
        body=body,
    )


@router.get(
    "/patient/{patient_id}/snapshots",
    response_model=PageSchema[ExaminationSnapshotRead],
)
async def list_snapshots(
    patient_id: str,
    map_id: str | None = Query(default=None, alias="mapId", max_length=60),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: ObservationService = Depends(get_observation_service),
) -> PageSchema[ExaminationSnapshotRead]:
    return await service.list_snapshots(
        user=user,
        patient_public_id=patient_id,
        map_id=map_id,
        page=PaginationParams(limit=limit, offset=offset),
    )


@router.get(
    "/encounter/{encounter_public_id}",
    response_model=PageSchema[ObservationRead],
)
async def list_encounter_observations(
    encounter_public_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: ObservationService = Depends(get_observation_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[ObservationRead]:
    return await service.list_by_encounter(
        user=user,
        encounter_public_id=encounter_public_id,
        page=PaginationParams(limit=limit, offset=offset),
        content_locale=content_locale,
    )


@router.get("/cohort", response_model=PageSchema[ObservationRead])
async def observation_cohort(
    concept_code: str = Query(alias="conceptCode", min_length=1, max_length=60),
    ordinal: int = Query(ge=-32768, le=32767),
    effective_from: datetime = Query(alias="effectiveFrom"),
    effective_to: datetime = Query(alias="effectiveTo"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: ObservationService = Depends(get_observation_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[ObservationRead]:
    return await service.list_cohort(
        user=user,
        concept_code=concept_code,
        ordinal_value=ordinal,
        effective_from=effective_from,
        effective_to=effective_to,
        page=PaginationParams(limit=limit, offset=offset),
        content_locale=content_locale,
    )


@router.patch("/{public_id}", response_model=ObservationRead)
async def update_observation(
    public_id: str,
    body: ObservationUpdate,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: ObservationService = Depends(get_observation_service),
    content_locale: str = Depends(get_content_locale),
) -> ObservationRead:
    return await service.update_observation(
        user=user,
        public_id=public_id,
        body=body,
        content_locale=content_locale,
    )


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(
    public_id: str,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: ObservationService = Depends(get_observation_service),
) -> Response:
    await service.delete_observation(user=user, public_id=public_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
