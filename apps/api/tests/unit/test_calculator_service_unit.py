"""Unit tests for CalculatorService with mocked persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ent.core.errors.exceptions import NotFoundError
from ent.core.repository.pagination import Page
from ent.core.schemas.base import PaginationParams
from ent.core.security.principal import CurrentUser
from ent.features.calculators.exceptions import (
    CalculatorInvalidInputError,
    CalculatorNotFoundError,
    CalculatorNotInteractiveError,
)
from ent.features.calculators.schemas.requests import CalculatorEvaluateRequest
from ent.features.calculators.service import CalculatorService
from ent.features.encounters.constants import LOCKED_STATUSES
from ent.features.encounters.exceptions import EncounterLockedError

PATIENT_PID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
ENCOUNTER_PID = "01ARZ3NDEKTSV4RRFFQ69G5FB0"


def _user() -> CurrentUser:
    return CurrentUser(
        user_id=10,
        user_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        session_id=20,
        session_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB2",
        clinic_id=1,
        clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB3",
        permissions=frozenset({"patient.read.clinic"}),
    )


@pytest.mark.asyncio
async def test_list_calculators_returns_page() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    service = CalculatorService(session)
    user = _user()
    page = await service.list_calculators(
        user=user,
        page=PaginationParams(limit=5, offset=0),
        domain=None,
        interactive_only=True,
    )
    assert page.page.total >= 10
    assert len(page.items) <= 5
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_get_calculator_unknown_raises() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    service = CalculatorService(session)
    with pytest.raises(CalculatorNotFoundError):
        await service.get_calculator(user=_user(), code="missing.code")


@pytest.mark.asyncio
async def test_evaluate_interactive_without_save() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    service = CalculatorService(session)
    body = CalculatorEvaluateRequest(inputs={"percent": 40})
    result = await service.evaluate(
        user=_user(),
        code="endoscopy.adenoid_obstruction",
        body=body,
    )
    assert result.value == "40"
    assert result.saved_result_id is None


@pytest.mark.asyncio
async def test_evaluate_non_interactive_raises() -> None:
    session = AsyncMock()
    service = CalculatorService(session)
    with pytest.raises(CalculatorNotInteractiveError):
        await service.evaluate(
            user=_user(),
            code="scoring.questionnaire_sum",
            body=CalculatorEvaluateRequest(inputs={}),
        )


@pytest.mark.asyncio
async def test_evaluate_invalid_input_maps_error() -> None:
    session = AsyncMock()
    service = CalculatorService(session)
    with pytest.raises(CalculatorInvalidInputError):
        await service.evaluate(
            user=_user(),
            code="endoscopy.adenoid_obstruction",
            body=CalculatorEvaluateRequest(inputs={}),
        )


@pytest.mark.asyncio
async def test_evaluate_save_with_locked_encounter_raises() -> None:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    service = CalculatorService(session)
    patient = SimpleNamespace(id=2, public_id=PATIENT_PID, created_by_id=10)
    encounter = SimpleNamespace(
        id=3,
        public_id=ENCOUNTER_PID,
        patient_id=2,
        status=next(iter(LOCKED_STATUSES)),
    )
    with (
        patch(
            "ent.features.calculators.service.PatientRepository.get_visible",
            new=AsyncMock(return_value=patient),
        ),
        patch(
            "ent.features.calculators.service.EncounterRepository.get_by_public_id",
            new=AsyncMock(return_value=encounter),
        ),
    ):
        with pytest.raises(EncounterLockedError):
            await service.evaluate(
                user=_user(),
                code="endoscopy.adenoid_obstruction",
                body=CalculatorEvaluateRequest(
                    inputs={"percent": 40},
                    patient_id=PATIENT_PID,
                    encounter_id=ENCOUNTER_PID,
                ),
            )


@pytest.mark.asyncio
async def test_list_patient_calculations() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    service = CalculatorService(session)
    patient = SimpleNamespace(id=2, public_id=PATIENT_PID, created_by_id=10)
    row = SimpleNamespace(
        public_id="01ARZ3NDEKTSV4RRFFQ69G5FC0",
        calculator_code="endoscopy.adenoid_obstruction",
        engine_version="1",
        value="40",
        unit="%",
        reference="",
        inputs={},
        flags=[],
        computed_at=datetime.now(UTC),
        patient_id=2,
        encounter_id=None,
    )
    page = Page(items=[row], total=1, limit=25, offset=0)
    with (
        patch(
            "ent.features.calculators.service.PatientRepository.get_visible",
            new=AsyncMock(return_value=patient),
        ),
        patch(
            "ent.features.calculators.service.CalculationResultRepository.list_for_patient",
            new=AsyncMock(return_value=page),
        ),
    ):
        out = await service.list_patient_calculations(
            user=_user(),
            patient_public_id=PATIENT_PID,
            page=PaginationParams(limit=25, offset=0),
            calculator_code=None,
            encounter_public_id=None,
        )
    assert out.page.total == 1
    assert out.items[0].value == "40"


@pytest.mark.asyncio
async def test_list_patient_calculations_patient_not_found() -> None:
    session = AsyncMock()
    service = CalculatorService(session)
    with patch(
        "ent.features.calculators.service.PatientRepository.get_visible",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(NotFoundError):
            await service.list_patient_calculations(
                user=_user(),
                patient_public_id=PATIENT_PID,
                page=PaginationParams(limit=25, offset=0),
                calculator_code=None,
                encounter_public_id=None,
            )


@pytest.mark.asyncio
async def test_evaluate_save_persists_row() -> None:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    audit = MagicMock()
    service = CalculatorService(session)
    service._audit = audit
    patient = SimpleNamespace(id=2, public_id=PATIENT_PID, created_by_id=10)
    repo_add = AsyncMock()

    async def _add(row: object) -> None:
        setattr(row, "public_id", "01ARZ3NDEKTSV4RRFFQ69G5FC1")
        setattr(row, "computed_at", datetime.now(UTC))

    repo_add.side_effect = _add
    calc_repo = MagicMock()
    calc_repo.add = repo_add

    with (
        patch(
            "ent.features.calculators.service.PatientRepository.get_visible",
            new=AsyncMock(return_value=patient),
        ),
        patch(
            "ent.features.calculators.service.CalculationResultRepository",
            return_value=calc_repo,
        ),
    ):
        result = await service.evaluate(
            user=_user(),
            code="endoscopy.adenoid_obstruction",
            body=CalculatorEvaluateRequest(
                inputs={"percent": 40},
                patient_id=PATIENT_PID,
            ),
        )
    assert result.saved_result_id == "01ARZ3NDEKTSV4RRFFQ69G5FC1"
    repo_add.assert_awaited()
