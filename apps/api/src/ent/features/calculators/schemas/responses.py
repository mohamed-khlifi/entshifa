"""Calculator HTTP response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ent.core.schemas.base import CamelModel


class CalculatorInputOptionRead(CamelModel):
    value: str
    label_key: str


class CalculatorInputFieldRead(CamelModel):
    name: str
    kind: str
    required: bool
    label_key: str
    unit: str | None = None
    min_value: str | None = None
    max_value: str | None = None
    default_value: str | None = None
    options: list[CalculatorInputOptionRead] = Field(default_factory=list)


class CalculatorSpecRead(CamelModel):
    code: str
    domain: str
    version: str
    reference: str
    unit: str | None
    formula: str
    interactive: bool
    inputs: list[CalculatorInputFieldRead] = Field(default_factory=list)


class CalculationFlagRead(CamelModel):
    code: str
    detail: dict[str, str] = Field(default_factory=dict)


class CalculationResultRead(CamelModel):
    code: str
    value: str
    unit: str | None
    inputs: dict[str, str]
    formula: str
    version: str
    reference: str
    flags: list[CalculationFlagRead] = Field(default_factory=list)
    saved_result_id: str | None = None
    computed_at: datetime | None = None


class SavedCalculationResultRead(CamelModel):
    public_id: str
    calculator_code: str
    engine_version: str
    inputs: dict[str, object]
    value: str
    unit: str | None
    flags: list[dict[str, object]]
    reference: str
    computed_at: datetime
    patient_id: str | None = None
    encounter_id: str | None = None
