"""Hearing devices and pediatric audiology HTTP endpoints (P4-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.audiology.dependencies import (
    get_hearing_device_service,
    idempotency_key,
)
from ent.features.audiology.device_service import HearingDeviceService
from ent.features.audiology.schemas.device_requests import (
    CandidacyConfirm,
    CandidacyEvaluate,
    HearingDeviceCreate,
    HearingDeviceUpdate,
    MilestonesUpdate,
    NewbornScreeningUpdate,
    OmeEpisodeCreate,
    OmeEpisodeUpdate,
)
from ent.features.audiology.schemas.device_responses import (
    CandidacyConfirmationRead,
    CandidacyEvaluationRead,
    HearingDeviceRead,
    OmeEpisodeRead,
    PediatricAudiologyRead,
    PediatricSummaryRead,
)
from ent.features.auth.dependencies import require

router = APIRouter(tags=["audiology"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get(
    "/api/v1/patients/{patient_id}/hearing-devices",
    response_model=PageSchema[HearingDeviceRead],
)
async def list_hearing_devices(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> PageSchema[HearingDeviceRead]:
    return await service.list_devices(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
    )


@router.post(
    "/api/v1/hearing-devices",
    response_model=HearingDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_hearing_device(
    body: HearingDeviceCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
    key: str | None = Depends(idempotency_key),
) -> HearingDeviceRead:
    return await service.create_device(user=user, body=body, idempotency_key=key)


@router.patch(
    "/api/v1/hearing-devices/{device_id}",
    response_model=HearingDeviceRead,
)
async def update_hearing_device(
    device_id: str,
    body: HearingDeviceUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> HearingDeviceRead:
    return await service.update_device(user=user, public_id=device_id, body=body)


@router.post(
    "/api/v1/audiology/candidacy/evaluate",
    response_model=CandidacyEvaluationRead,
)
async def evaluate_candidacy(
    body: CandidacyEvaluate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> CandidacyEvaluationRead:
    return await service.evaluate_candidacy(user=user, body=body)


@router.post(
    "/api/v1/patients/{patient_id}/audiology/candidacy/confirm",
    response_model=CandidacyConfirmationRead,
)
async def confirm_candidacy(
    patient_id: str,
    body: CandidacyConfirm,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_INTERPRET)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> CandidacyConfirmationRead:
    return await service.confirm_candidacy(
        user=user,
        patient_public_id=patient_id,
        body=body,
    )


@router.get(
    "/api/v1/patients/{patient_id}/audiology/pediatric",
    response_model=PediatricSummaryRead,
)
async def get_pediatric_audiology(
    patient_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> PediatricSummaryRead:
    return await service.get_pediatric_summary(
        user=user,
        patient_public_id=patient_id,
        ome_page=_page(limit, offset),
    )


@router.put(
    "/api/v1/patients/{patient_id}/audiology/pediatric/screening",
    response_model=PediatricAudiologyRead,
)
async def update_newborn_screening(
    patient_id: str,
    body: NewbornScreeningUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> PediatricAudiologyRead:
    return await service.update_newborn_screening(
        user=user,
        patient_public_id=patient_id,
        body=body,
    )


@router.put(
    "/api/v1/patients/{patient_id}/audiology/pediatric/milestones",
    response_model=PediatricAudiologyRead,
)
async def update_pediatric_milestones(
    patient_id: str,
    body: MilestonesUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> PediatricAudiologyRead:
    return await service.update_milestones(
        user=user,
        patient_public_id=patient_id,
        body=body,
    )


@router.post(
    "/api/v1/ome-episodes",
    response_model=OmeEpisodeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_ome_episode(
    body: OmeEpisodeCreate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
    key: str | None = Depends(idempotency_key),
) -> OmeEpisodeRead:
    return await service.create_ome_episode(user=user, body=body, idempotency_key=key)


@router.patch(
    "/api/v1/ome-episodes/{ome_id}",
    response_model=OmeEpisodeRead,
)
async def update_ome_episode(
    ome_id: str,
    body: OmeEpisodeUpdate,
    user: CurrentUser = Depends(require(Permission.AUDIOLOGY_ENTER)),
    service: HearingDeviceService = Depends(get_hearing_device_service),
) -> OmeEpisodeRead:
    return await service.update_ome_episode(user=user, public_id=ome_id, body=body)
