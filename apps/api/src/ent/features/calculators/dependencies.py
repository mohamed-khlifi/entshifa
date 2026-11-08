"""Calculator FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.calculators.service import CalculatorService


def get_calculator_service(
    session: AsyncSession = Depends(get_session),
) -> CalculatorService:
    return CalculatorService(session=session)
