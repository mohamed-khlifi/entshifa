"""Calculator registry HTTP endpoints (P5-05)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.calculators.dependencies import get_calculator_service
from ent.features.calculators.schemas.requests import CalculatorEvaluateRequest
from ent.features.calculators.schemas.responses import (
    CalculationResultRead,
    CalculatorSpecRead,
    SavedCalculationResultRead,
)
from ent.features.calculators.service import CalculatorService

router = APIRouter(tags=["calculators"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


@router.get("/api/v1/calculators", response_model=PageSchema[CalculatorSpecRead])
async def list_calculators(
    domain: str | None = Query(default=None, max_length=40),
    interactive_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: CalculatorService = Depends(get_calculator_service),
) -> PageSchema[CalculatorSpecRead]:
    return await service.list_calculators(
        user=user,
        page=_page(limit, offset),
        domain=domain,
        interactive_only=interactive_only,
    )


@router.get("/api/v1/calculators/{code}", response_model=CalculatorSpecRead)
async def get_calculator(
    code: str,
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: CalculatorService = Depends(get_calculator_service),
) -> CalculatorSpecRead:
    return await service.get_calculator(user=user, code=code)


@router.post("/api/v1/calculators/{code}", response_model=CalculationResultRead)
async def evaluate_calculator(
    code: str,
    body: CalculatorEvaluateRequest,
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: CalculatorService = Depends(get_calculator_service),
) -> CalculationResultRead:
    return await service.evaluate(user=user, code=code, body=body)


@router.get(
    "/api/v1/patients/{patient_id}/calculations",
    response_model=PageSchema[SavedCalculationResultRead],
)
async def list_patient_calculations(
    patient_id: str,
    calculator_code: str | None = Query(default=None, max_length=60),
    encounter_id: str | None = Query(default=None, max_length=26),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PATIENT_READ_CLINIC)),
    service: CalculatorService = Depends(get_calculator_service),
) -> PageSchema[SavedCalculationResultRead]:
    return await service.list_patient_calculations(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        calculator_code=calculator_code,
        encounter_public_id=encounter_id,
    )
