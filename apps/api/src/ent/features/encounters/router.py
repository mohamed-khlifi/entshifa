"""Encounter HTTP endpoints (P2-02)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.encounters.dependencies import (
    get_content_locale,
    get_encounter_service,
)
from ent.features.encounters.schemas.requests import (
    EncounterAddendumCreate,
    EncounterCopyForward,
    EncounterCreate,
    EncounterPatch,
    EncounterSign,
)
from ent.features.encounters.schemas.responses import EncounterRead
from ent.features.encounters.service import EncounterService

router = APIRouter(tags=["encounters"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.post(
    "/api/v1/encounters",
    response_model=EncounterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_encounter(
    body: EncounterCreate,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_CREATE)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterRead:
    return await service.create_encounter(
        user=user, body=body, content_locale=content_locale
    )


@router.get(
    "/api/v1/patients/{patient_id}/encounters",
    response_model=PageSchema[EncounterRead],
)
async def list_patient_encounters(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[EncounterRead]:
    return await service.list_for_patient(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        content_locale=content_locale,
    )


@router.get("/api/v1/encounters/{encounter_id}", response_model=EncounterRead)
async def get_encounter(
    encounter_id: str,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterRead:
    return await service.get_encounter(
        user=user, public_id=encounter_id, content_locale=content_locale
    )


@router.patch("/api/v1/encounters/{encounter_id}", response_model=EncounterRead)
async def patch_encounter(
    encounter_id: str,
    body: EncounterPatch,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterRead:
    return await service.patch_encounter(
        user=user,
        public_id=encounter_id,
        body=body,
        content_locale=content_locale,
    )


@router.post("/api/v1/encounters/{encounter_id}/sign", response_model=EncounterRead)
async def sign_encounter(
    encounter_id: str,
    body: EncounterSign,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_SIGN)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterRead:
    return await service.sign_encounter(
        user=user,
        public_id=encounter_id,
        body=body,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/encounters/{encounter_id}/addenda",
    response_model=EncounterRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_encounter_addendum(
    encounter_id: str,
    body: EncounterAddendumCreate,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_AMEND)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterRead:
    return await service.add_addendum(
        user=user,
        public_id=encounter_id,
        body=body,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/encounters/{encounter_id}/copy-forward",
    response_model=EncounterRead,
    status_code=status.HTTP_201_CREATED,
)
async def copy_encounter_forward(
    encounter_id: str,
    body: EncounterCopyForward,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_CREATE)),
    service: EncounterService = Depends(get_encounter_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterRead:
    return await service.copy_forward(
        user=user,
        public_id=encounter_id,
        body=body,
        content_locale=content_locale,
    )
