"""Map pure calculator specs and rows to API schemas."""

from __future__ import annotations

from datetime import datetime

from ent.engines.calculator_catalog import (
    CalculatorInputField,
    CalculatorInputOption,
    CalculatorSpec,
)
from ent.engines.results import CalculationResult, Flag
from ent.features.calculators.schemas.responses import (
    CalculationFlagRead,
    CalculationResultRead,
    CalculatorInputFieldRead,
    CalculatorInputOptionRead,
    CalculatorSpecRead,
    SavedCalculationResultRead,
)
from ent.features.prescriptions.models import CalculationResultRow


def to_option(option: CalculatorInputOption) -> CalculatorInputOptionRead:
    return CalculatorInputOptionRead(value=option.value, label_key=option.label_key)


def to_field(field: CalculatorInputField) -> CalculatorInputFieldRead:
    return CalculatorInputFieldRead(
        name=field.name,
        kind=field.kind,
        required=field.required,
        label_key=field.label_key,
        unit=field.unit,
        min_value=field.min_value,
        max_value=field.max_value,
        default_value=field.default_value,
        options=[to_option(option) for option in field.options],
    )


def to_spec_read(spec: CalculatorSpec) -> CalculatorSpecRead:
    return CalculatorSpecRead(
        code=spec.code,
        domain=spec.domain,
        version=spec.version,
        reference=spec.reference,
        unit=spec.unit,
        formula=spec.formula,
        interactive=spec.interactive,
        inputs=[to_field(field) for field in spec.inputs],
    )


def to_flag(flag: Flag) -> CalculationFlagRead:
    return CalculationFlagRead(code=flag.code, detail=dict(flag.detail))


def to_result_read(
    result: CalculationResult,
    *,
    saved_result_id: str | None = None,
    computed_at: datetime | None = None,
) -> CalculationResultRead:
    return CalculationResultRead(
        code=result.code,
        value=result.value,
        unit=result.unit,
        inputs=dict(result.inputs),
        formula=result.formula,
        version=result.version,
        reference=result.reference,
        flags=[to_flag(flag) for flag in result.flags],
        saved_result_id=saved_result_id,
        computed_at=computed_at,
    )


def to_saved_read(
    row: CalculationResultRow,
    *,
    patient_public_id: str | None,
    encounter_public_id: str | None,
) -> SavedCalculationResultRead:
    return SavedCalculationResultRead(
        public_id=row.public_id,
        calculator_code=row.calculator_code,
        engine_version=row.engine_version,
        inputs=dict(row.inputs),
        value=row.value,
        unit=row.unit,
        flags=list(row.flags),
        reference=row.reference,
        computed_at=row.computed_at,
        patient_id=patient_public_id,
        encounter_id=encounter_public_id,
    )
