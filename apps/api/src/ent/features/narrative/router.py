"""Examination narrative HTTP endpoint (P2-04)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.narrative.dependencies import (
    get_content_locale,
    get_narrative_service,
)
from ent.features.narrative.schemas import NarrativeRenderRead, NarrativeRenderRequest
from ent.features.narrative.service import NarrativeService

router = APIRouter(prefix="/api/v1/narrative", tags=["narrative"])


@router.post("/render", response_model=NarrativeRenderRead)
async def render_narrative(
    body: NarrativeRenderRequest,
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: NarrativeService = Depends(get_narrative_service),
    content_locale: str = Depends(get_content_locale),
) -> NarrativeRenderRead:
    return await service.render(user=user, body=body, content_locale=content_locale)
