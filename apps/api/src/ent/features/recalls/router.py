"""Manual recall endpoints (P2-11)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.recalls.dependencies import get_recall_service
from ent.features.recalls.schemas.requests import (
    RecallActionCreate,
    RecallBook,
    RecallBucket,
    RecallCancel,
    RecallComplete,
    RecallCreate,
    RecallUpdate,
)
from ent.features.recalls.schemas.responses import RecallRead, RecallSummaryRead
from ent.features.recalls.service import RecallService

router = APIRouter(tags=["recalls"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


def _key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    if idempotency_key is None:
        return None
    return idempotency_key[:80]


@router.get("/api/v1/recalls/summary", response_model=RecallSummaryRead)
async def recall_summary(
    user: CurrentUser = Depends(require(Permission.RECALL_READ)),
    service: RecallService = Depends(get_recall_service),
) -> RecallSummaryRead:
    return await service.get_summary(user=user)


@router.get("/api/v1/recalls", response_model=PageSchema[RecallRead])
async def list_recalls(
    bucket: RecallBucket | None = Query(default=None),
    status: str | None = Query(default=None, max_length=20),
    action_type: str | None = Query(default=None, max_length=30),
    patient_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.RECALL_READ)),
    service: RecallService = Depends(get_recall_service),
) -> PageSchema[RecallRead]:
    return await service.list_recalls(
        user=user,
        page=_page(limit, offset),
        bucket=bucket,
        status=status,
        action_type=action_type,
        patient_public_id=patient_id,
    )


@router.post("/api/v1/recalls", response_model=RecallRead, status_code=201)
async def create_recall(
    body: RecallCreate,
    user: CurrentUser = Depends(require(Permission.RECALL_WRITE)),
    service: RecallService = Depends(get_recall_service),
    idempotency_key: str | None = Depends(_key),
) -> RecallRead:
    return await service.create_recall(
        user=user, body=body, idempotency_key=idempotency_key
    )


@router.get("/api/v1/recalls/{recall_id}", response_model=RecallRead)
async def get_recall(
    recall_id: str,
    user: CurrentUser = Depends(require(Permission.RECALL_READ)),
    service: RecallService = Depends(get_recall_service),
) -> RecallRead:
    return await service.get_recall(user=user, public_id=recall_id)


@router.patch("/api/v1/recalls/{recall_id}", response_model=RecallRead)
async def update_recall(
    recall_id: str,
    body: RecallUpdate,
    user: CurrentUser = Depends(require(Permission.RECALL_WRITE)),
    service: RecallService = Depends(get_recall_service),
) -> RecallRead:
    return await service.update_recall(user=user, public_id=recall_id, body=body)


@router.post("/api/v1/recalls/{recall_id}/actions", response_model=RecallRead)
async def log_recall_action(
    recall_id: str,
    body: RecallActionCreate,
    user: CurrentUser = Depends(require(Permission.RECALL_WRITE)),
    service: RecallService = Depends(get_recall_service),
) -> RecallRead:
    return await service.log_action(user=user, public_id=recall_id, body=body)


@router.post("/api/v1/recalls/{recall_id}/book", response_model=RecallRead)
async def book_recall(
    recall_id: str,
    body: RecallBook,
    user: CurrentUser = Depends(require(Permission.RECALL_WRITE)),
    service: RecallService = Depends(get_recall_service),
) -> RecallRead:
    return await service.book_appointment(user=user, public_id=recall_id, body=body)


@router.post("/api/v1/recalls/{recall_id}/cancel", response_model=RecallRead)
async def cancel_recall(
    recall_id: str,
    body: RecallCancel,
    user: CurrentUser = Depends(require(Permission.RECALL_WRITE)),
    service: RecallService = Depends(get_recall_service),
) -> RecallRead:
    return await service.cancel_recall(user=user, public_id=recall_id, body=body)


@router.post("/api/v1/recalls/{recall_id}/complete", response_model=RecallRead)
async def complete_recall(
    recall_id: str,
    body: RecallComplete,
    user: CurrentUser = Depends(require(Permission.RECALL_WRITE)),
    service: RecallService = Depends(get_recall_service),
) -> RecallRead:
    return await service.complete_recall(user=user, public_id=recall_id, body=body)
