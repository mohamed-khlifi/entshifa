"""Body mass index (feature spec §12.5)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ent.engines.general.errors import GeneralCalculatorInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "general.bmi"
REFERENCE = "WHO Technical Report Series 894 (2000). Feature specification §12.5."
FORMULA = "BMI = weight_kg / (height_cm / 100) ^ 2"
_BMI_PRECISION = Decimal("0.01")
_ZERO = Decimal("0")


def _band(bmi: Decimal) -> str:
    if bmi < Decimal("18.5"):
        return "underweight"
    if bmi < Decimal("25"):
        return "normal"
    if bmi < Decimal("30"):
        return "overweight"
    if bmi < Decimal("35"):
        return "obesity_class_i"
    if bmi < Decimal("40"):
        return "obesity_class_ii"
    return "obesity_class_iii"


def score(*, weight_kg: Decimal, height_cm: Decimal) -> CalculationResult:
    """Compute BMI from height and weight. Does not substitute missing vitals."""

    if not weight_kg.is_finite() or not height_cm.is_finite():
        raise GeneralCalculatorInputError("general.bmi_input_invalid")
    if weight_kg <= _ZERO or weight_kg > Decimal("500"):
        raise GeneralCalculatorInputError("general.weight_out_of_range")
    if height_cm < Decimal("30") or height_cm > Decimal("250"):
        raise GeneralCalculatorInputError("general.height_out_of_range")
    meters = height_cm / Decimal("100")
    if meters <= _ZERO:
        raise GeneralCalculatorInputError("general.height_out_of_range")
    bmi = (weight_kg / (meters * meters)).quantize(
        _BMI_PRECISION, rounding=ROUND_HALF_UP
    )
    band = _band(bmi)
    return CalculationResult(
        code=CODE,
        value=format(bmi, "f"),
        unit="kg/m2",
        inputs={
            "weight_kg": format(weight_kg, "f"),
            "height_cm": format(height_cm, "f"),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(Flag(code="band", detail={"band": band}),),
    )
