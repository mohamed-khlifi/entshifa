from fastapi import APIRouter, Depends, Response, status

from ent.features.health.dependencies import get_health_service_for_request
from ent.features.health.schemas.responses import (
    LiveHealthResponse,
    ReadyHealthResponse,
)
from ent.features.health.service import HealthService

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=LiveHealthResponse)
async def health_live(
    service: HealthService = Depends(get_health_service_for_request),
) -> LiveHealthResponse:
    return service.live()


@router.get("/health/ready", response_model=ReadyHealthResponse)
async def health_ready(
    response: Response,
    service: HealthService = Depends(get_health_service_for_request),
) -> ReadyHealthResponse:
    body, is_ready = await service.ready()
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return body
