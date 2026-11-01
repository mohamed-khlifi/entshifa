"""Speech audiometry HTTP endpoints (P4-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.audiology.dependencies import (
    get_speech_audiometry_service,
    idempotency_key,
)
from ent.features.audiology.schemas.test_requests import (
    SpeechAudiometryCreate,
    SpeechAudiometryUpdate,
)
from ent.features.audiology.schemas.test_responses import SpeechAudiometryRead
from ent.features.audiology.speech_service import SpeechAudiometryService
from ent.features.auth.dependencies import require

router = APIRouter(tags=["audiology"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/speech-audiometry",
    response_model=PageSchema[SpeechAudiometryRead],
)
async def list_speech_audiometry(
    patient_id: str | None = Query(default=None, min_length=26, max_length=26),
    encounter_id: str | None = Query(default=None, min_length=26, max_length=26),
    audiogram_id: str | None = Query(default=None, min_length=26, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: SpeechAudiometryService = Depends(get_speech_audiometry_service),
) -> PageSchema[SpeechAudiometryRead]:
    return await service.list_speech_audiometry(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
        encounter_public_id=encounter_id,
        audiogram_public_id=audiogram_id,
    )


@router.get(
    "/api/v1/patients/{patient_id}/speech-audiometry",
    response_model=PageSchema[SpeechAudiometryRead],
)
async def list_patient_speech_audiometry(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: SpeechAudiometryService = Depends(get_speech_audiometry_service),
) -> PageSchema[SpeechAudiometryRead]:
    return await service.list_speech_audiometry(
        user=user,
        page=_page(limit, offset),
        patient_public_id=patient_id,
    )


@router.post(
    "/api/v1/speech-audiometry",
    response_model=SpeechAudiometryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_speech_audiometry(
    body: SpeechAudiometryCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: SpeechAudiometryService = Depends(get_speech_audiometry_service),
    key: str | None = Depends(idempotency_key),
) -> SpeechAudiometryRead:
    return await service.create_speech_audiometry(
        user=user,
        body=body,
        idempotency_key=key,
    )


@router.get(
    "/api/v1/speech-audiometry/{speech_id}",
    response_model=SpeechAudiometryRead,
)
async def get_speech_audiometry(
    speech_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: SpeechAudiometryService = Depends(get_speech_audiometry_service),
) -> SpeechAudiometryRead:
    return await service.get_speech_audiometry(user=user, public_id=speech_id)


@router.put(
    "/api/v1/speech-audiometry/{speech_id}",
    response_model=SpeechAudiometryRead,
)
async def update_speech_audiometry(
    speech_id: str,
    body: SpeechAudiometryUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: SpeechAudiometryService = Depends(get_speech_audiometry_service),
) -> SpeechAudiometryRead:
    return await service.update_speech_audiometry(
        user=user,
        public_id=speech_id,
        body=body,
    )
