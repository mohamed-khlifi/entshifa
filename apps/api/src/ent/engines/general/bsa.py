"""Body surface area (feature spec §12.5)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from math import sqrt
from typing import Literal

from ent.engines.general.errors import GeneralCalculatorInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "general.bsa"
REFERENCE = (
    "Mosteller RD. N Engl J Med 1987;317(17):1098. "
    "Du Bois D, Du Bois EF. Arch Intern Med 1916;17:863-871. "
    "Feature specification §12.5."
)
FORMULA = (
    "mosteller: sqrt((height_cm * weight_kg) / 3600); "
    "dubois: 0.007184 * weight_kg^0.425 * height_cm^0.725"
)
_BSA_PRECISION = Decimal("0.01")
_ZERO = Decimal("0")
Method = Literal["mosteller", "dubois"]


def _mosteller(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    product = height_cm * weight_kg
    value = Decimal(str(sqrt(float(product / Decimal("3600")))))
    return value.quantize(_BSA_PRECISION, rounding=ROUND_HALF_UP)


def _dubois(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    w = float(weight_kg)
    h = float(height_cm)
    value = 0.007184 * (w**0.425) * (h**0.725)
    return Decimal(str(value)).quantize(_BSA_PRECISION, rounding=ROUND_HALF_UP)


def score(
    *,
    weight_kg: Decimal,
    height_cm: Decimal,
    method: Method = "mosteller",
) -> CalculationResult:
    """Compute BSA. Method must be explicit."""

    if not weight_kg.is_finite() or not height_cm.is_finite():
        raise GeneralCalculatorInputError("general.bsa_input_invalid")
    if weight_kg <= _ZERO or weight_kg > Decimal("500"):
        raise GeneralCalculatorInputError("general.weight_out_of_range")
    if height_cm < Decimal("20") or height_cm > Decimal("250"):
        raise GeneralCalculatorInputError("general.height_out_of_range")
    if method not in ("mosteller", "dubois"):
        raise GeneralCalculatorInputError("general.bsa_method_invalid")
    bsa = (
        _mosteller(weight_kg, height_cm)
        if method == "mosteller"
        else _dubois(weight_kg, height_cm)
    )
    return CalculationResult(
        code=CODE,
        value=format(bsa, "f"),
        unit="m2",
        inputs={
            "weight_kg": format(weight_kg, "f"),
            "height_cm": format(height_cm, "f"),
            "method": method,
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(Flag(code="method", detail={"method": method}),),
    )
