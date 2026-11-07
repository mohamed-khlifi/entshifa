"""Questionnaire instrument endpoints (P5-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.questionnaires.dependencies import get_questionnaire_service
from ent.features.questionnaires.schemas.requests import (
    InstrumentCreate,
    InstrumentScoreRequest,
    InstrumentTranslationUpsert,
    InstrumentVersionCreate,
)
from ent.features.questionnaires.schemas.responses import (
    InstrumentDetailRead,
    InstrumentLocalizedRead,
    InstrumentScoreRead,
    InstrumentSummaryRead,
)
from ent.features.questionnaires.service import QuestionnaireService

router = APIRouter(tags=["instruments"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get("/api/v1/instruments", response_model=PageSchema[InstrumentSummaryRead])
async def list_instruments(
    category: str | None = Query(default=None, max_length=30),
    respondent: str | None = Query(default=None, max_length=20),
    locale: str | None = Query(default=None, max_length=10),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> PageSchema[InstrumentSummaryRead]:
    return await service.list_instruments(
        user=user,
        page=_page(limit, offset),
        category=category,
        respondent=respondent,
        locale=locale,
    )


@router.post(
    "/api/v1/instruments", response_model=InstrumentDetailRead, status_code=201
)
async def create_instrument(
    body: InstrumentCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> InstrumentDetailRead:
    return await service.create_instrument(user=user, body=body)


@router.get(
    "/api/v1/instruments/by-code/{code}",
    response_model=InstrumentDetailRead | InstrumentLocalizedRead,
)
async def get_instrument_by_code(
    code: str,
    locale: str | None = Query(default=None, max_length=10),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> InstrumentDetailRead | InstrumentLocalizedRead:
    return await service.get_instrument_by_code(user=user, code=code, locale=locale)


@router.get("/api/v1/instruments/{instrument_id}", response_model=InstrumentDetailRead)
async def get_instrument(
    instrument_id: str,
    locale: str | None = Query(default=None, max_length=10),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> InstrumentDetailRead | InstrumentLocalizedRead:
    return await service.get_instrument(
        user=user,
        public_id=instrument_id,
        locale=locale,
    )


@router.post(
    "/api/v1/instruments/{instrument_id}/versions",
    response_model=InstrumentDetailRead,
    status_code=201,
)
async def create_instrument_version(
    instrument_id: str,
    body: InstrumentVersionCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> InstrumentDetailRead:
    return await service.create_instrument_version(
        user=user,
        public_id=instrument_id,
        body=body,
    )


@router.put(
    "/api/v1/instruments/{instrument_id}/translations/{locale}",
    response_model=InstrumentLocalizedRead,
)
async def upsert_instrument_translations(
    instrument_id: str,
    locale: str,
    body: InstrumentTranslationUpsert,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> InstrumentLocalizedRead:
    return await service.upsert_translations(
        user=user,
        public_id=instrument_id,
        locale=locale,
        body=body,
    )


@router.post(
    "/api/v1/instruments/{instrument_id}/score",
    response_model=InstrumentScoreRead,
)
async def score_instrument(
    instrument_id: str,
    body: InstrumentScoreRequest,
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> InstrumentScoreRead:
    return await service.score_instrument(
        user=user,
        public_id=instrument_id,
        body=body,
    )
