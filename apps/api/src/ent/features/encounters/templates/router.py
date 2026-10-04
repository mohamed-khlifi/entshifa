"""Encounter template HTTP endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status

from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.encounters.dependencies import (
    get_content_locale,
    get_encounter_template_service,
)
from ent.features.encounters.schemas.requests import (
    EncounterTemplateOverrideWrite,
    EncounterTemplateRouteRequest,
)
from ent.features.encounters.schemas.responses import EncounterTemplateRead
from ent.features.encounters.templates.service import EncounterTemplateService

router = APIRouter(tags=["encounter-templates"])


@router.get(
    "/api/v1/encounter-templates",
    response_model=list[EncounterTemplateRead],
)
async def list_encounter_templates(
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterTemplateService = Depends(get_encounter_template_service),
    content_locale: str = Depends(get_content_locale),
) -> list[EncounterTemplateRead]:
    return await service.list_templates(
        user=user,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/encounter-templates/route",
    response_model=EncounterTemplateRead,
)
async def route_encounter_template(
    body: EncounterTemplateRouteRequest,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterTemplateService = Depends(get_encounter_template_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterTemplateRead:
    return await service.route_by_complaint(
        user=user,
        body=body,
        content_locale=content_locale,
    )


@router.get(
    "/api/v1/encounter-templates/{public_id}",
    response_model=EncounterTemplateRead,
)
async def get_encounter_template(
    public_id: str,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterTemplateService = Depends(get_encounter_template_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterTemplateRead:
    return await service.get_by_public_id(
        user=user,
        public_id=public_id,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/encounter-templates/{code}/override",
    response_model=EncounterTemplateRead,
    status_code=status.HTTP_200_OK,
)
async def override_encounter_template(
    code: str,
    body: EncounterTemplateOverrideWrite,
    scope: Literal["doctor", "clinic"] = Query(default="doctor"),
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterTemplateService = Depends(get_encounter_template_service),
    content_locale: str = Depends(get_content_locale),
) -> EncounterTemplateRead:
    return await service.override_template(
        user=user,
        base_code=code,
        body=body,
        content_locale=content_locale,
        scope=scope,
    )


@router.delete(
    "/api/v1/encounter-templates/{code}/override",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_encounter_template_override(
    code: str,
    scope: Literal["doctor", "clinic"] = Query(default="doctor"),
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: EncounterTemplateService = Depends(get_encounter_template_service),
) -> Response:
    await service.reset_override(
        user=user,
        base_code=code,
        scope=scope,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
