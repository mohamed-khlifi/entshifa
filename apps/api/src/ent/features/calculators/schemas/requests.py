"""Calculator HTTP request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ent.core.schemas.base import CamelModel


class CalculatorEvaluateRequest(CamelModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    save_to_consultation: bool = False
    patient_id: str | None = Field(default=None, max_length=26)
    encounter_id: str | None = Field(default=None, max_length=26)
