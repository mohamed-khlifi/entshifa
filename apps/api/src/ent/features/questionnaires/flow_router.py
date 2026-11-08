"""Authenticated questionnaire invitation and response endpoints (P5-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.questionnaires.dependencies import get_questionnaire_flow_service
from ent.features.questionnaires.flow_service import QuestionnaireFlowService
from ent.features.questionnaires.schemas.flow_requests import (
    QuestionnaireInvitationCreate,
    QuestionnaireStaffResponseCreate,
)
from ent.features.questionnaires.schemas.flow_responses import (
    QuestionnaireInvitationCreatedRead,
    QuestionnaireInvitationRead,
    QuestionnaireResponseDetailRead,
    QuestionnaireResponseRead,
)

router = APIRouter(tags=["questionnaire-flow"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


def _idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    if idempotency_key is None:
        return None
    return idempotency_key[:80]


@router.post(
    "/api/v1/patients/{patient_id}/questionnaire-invitations",
    response_model=QuestionnaireInvitationCreatedRead,
    status_code=201,
)
async def create_questionnaire_invitation(
    patient_id: str,
    body: QuestionnaireInvitationCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    idempotency_key: str | None = Depends(_idempotency_key),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> QuestionnaireInvitationCreatedRead:
    return await service.create_invitation(
        user=user,
        patient_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.get(
    "/api/v1/patients/{patient_id}/questionnaire-invitations",
    response_model=PageSchema[QuestionnaireInvitationRead],
)
async def list_questionnaire_invitations(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> PageSchema[QuestionnaireInvitationRead]:
    return await service.list_invitations(
        user=user,
        patient_id=patient_id,
        page=_page(limit, offset),
    )


@router.post(
    "/api/v1/patients/{patient_id}/questionnaire-responses",
    response_model=QuestionnaireResponseRead,
    status_code=201,
)
async def create_questionnaire_response(
    patient_id: str,
    body: QuestionnaireStaffResponseCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    idempotency_key: str | None = Depends(_idempotency_key),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> QuestionnaireResponseRead:
    return await service.create_staff_response(
        user=user,
        patient_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.get(
    "/api/v1/patients/{patient_id}/questionnaire-responses",
    response_model=PageSchema[QuestionnaireResponseRead],
)
async def list_questionnaire_responses(
    patient_id: str,
    instrument_code: str | None = Query(default=None, max_length=40),
    encounter_id: str | None = Query(default=None, max_length=26),
    locale: str | None = Query(default=None, max_length=10),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> PageSchema[QuestionnaireResponseRead]:
    return await service.list_responses(
        user=user,
        patient_id=patient_id,
        instrument_code=instrument_code,
        encounter_id=encounter_id,
        page=_page(limit, offset),
        display_locale=locale,
    )


@router.get(
    "/api/v1/questionnaire-responses/{response_id}",
    response_model=QuestionnaireResponseDetailRead,
)
async def get_questionnaire_response(
    response_id: str,
    locale: str | None = Query(default=None, max_length=10),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> QuestionnaireResponseDetailRead:
    return await service.get_response(
        user=user,
        response_id=response_id,
        display_locale=locale,
    )
