"""Public questionnaire endpoints (no authentication, P5-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ent.features.auth.dependencies import get_client_ip
from ent.features.questionnaires.dependencies import get_questionnaire_flow_service
from ent.features.questionnaires.flow_service import QuestionnaireFlowService
from ent.features.questionnaires.schemas.flow_requests import PublicQuestionnaireSubmit
from ent.features.questionnaires.schemas.flow_responses import (
    PublicQuestionnaireCompletionRead,
    PublicQuestionnaireSessionRead,
)

router = APIRouter(tags=["public-questionnaires"])


@router.get(
    "/api/v1/public/questionnaires/{token}",
    response_model=PublicQuestionnaireSessionRead,
)
async def get_public_questionnaire_session(
    token: str,
    ip_address: str | None = Depends(get_client_ip),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> PublicQuestionnaireSessionRead:
    return await service.public_get_session(raw_token=token, ip_address=ip_address)


@router.post(
    "/api/v1/public/questionnaires/{token}/submit",
    response_model=PublicQuestionnaireCompletionRead,
    status_code=201,
)
async def submit_public_questionnaire(
    token: str,
    body: PublicQuestionnaireSubmit,
    ip_address: str | None = Depends(get_client_ip),
    service: QuestionnaireFlowService = Depends(get_questionnaire_flow_service),
) -> PublicQuestionnaireCompletionRead:
    return await service.public_submit(
        raw_token=token,
        body=body,
        ip_address=ip_address,
    )
