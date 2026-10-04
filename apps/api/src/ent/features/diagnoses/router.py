"""Diagnosis favourites and problem-list promotion (P2-07)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ent.core.schemas.base import PageSchema
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.diagnoses.dependencies import get_diagnosis_service
from ent.features.diagnoses.schemas.requests import DiagnosisFavoriteReplace
from ent.features.diagnoses.schemas.responses import (
    DiagnosisFavoriteRead,
    DiagnosisRead,
)
from ent.features.diagnoses.service import DiagnosisService
from ent.features.encounters.dependencies import get_content_locale

router = APIRouter(tags=["diagnoses"])


@router.get(
    "/api/v1/diagnoses/favorites",
    response_model=PageSchema[DiagnosisFavoriteRead],
)
async def list_diagnosis_favorites(
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: DiagnosisService = Depends(get_diagnosis_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[DiagnosisFavoriteRead]:
    return await service.list_favorites(user=user, content_locale=content_locale)


@router.put(
    "/api/v1/diagnoses/favorites",
    response_model=PageSchema[DiagnosisFavoriteRead],
)
async def replace_diagnosis_favorites(
    body: DiagnosisFavoriteReplace,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: DiagnosisService = Depends(get_diagnosis_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[DiagnosisFavoriteRead]:
    return await service.replace_favorites(
        user=user, body=body, content_locale=content_locale
    )


@router.post(
    "/api/v1/encounters/{encounter_id}/diagnoses/{diagnosis_id}/promote",
    response_model=DiagnosisRead,
)
async def promote_diagnosis(
    encounter_id: str,
    diagnosis_id: str,
    user: CurrentUser = Depends(require(Permission.ENCOUNTER_WRITE)),
    service: DiagnosisService = Depends(get_diagnosis_service),
    content_locale: str = Depends(get_content_locale),
) -> DiagnosisRead:
    return await service.promote(
        user=user,
        encounter_public_id=encounter_id,
        diagnosis_public_id=diagnosis_id,
        content_locale=content_locale,
    )
