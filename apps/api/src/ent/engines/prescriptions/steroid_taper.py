"""Day-by-day dose decrement from caller-supplied step parameters.

This is not a prednisolone protocol. The start, step, dwell, and floor
come from the request or from formulary_entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.prescriptions.errors import EngineInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
REFERENCE = (
    "Hold dose for days_per_step, then subtract step_mg, "
    "while dose >= minimum_mg and dose > 0. "
    "Parameters are caller inputs. Not a steroid protocol. P2-08."
)
CODE = "prescriptions.steroid_taper"
FORMULA = (
    "repeat days_per_step at the current dose, then dose = dose - step_mg, "
    "stop when dose < minimum_mg or dose <= 0"
)
_MG = Decimal("0.001")
_ZERO = Decimal("0")
_MAX_DAYS = 366


@dataclass(frozen=True, slots=True)
class TaperInput:
    start_mg: Decimal
    step_mg: Decimal
    days_per_step: int
    minimum_mg: Decimal


@dataclass(frozen=True, slots=True)
class TaperDay:
    day_number: int
    dose_mg: Decimal


@dataclass(frozen=True, slots=True)
class TaperResult:
    calculation: CalculationResult
    days: tuple[TaperDay, ...]


def _mg(value: Decimal) -> Decimal:
    return value.quantize(_MG, rounding=ROUND_HALF_UP)


def generate_steroid_taper(data: TaperInput) -> TaperResult:
    """Expand a decrement into one row per calendar day of the schedule."""

    if (
        not data.start_mg.is_finite()
        or not data.step_mg.is_finite()
        or not data.minimum_mg.is_finite()
    ):
        raise EngineInputError("prescription.taper_input_invalid")
    if data.start_mg <= _ZERO or data.step_mg <= _ZERO:
        raise EngineInputError("prescription.taper_input_invalid")
    if data.days_per_step < 1 or data.minimum_mg < _ZERO:
        raise EngineInputError("prescription.taper_input_invalid")
    if data.start_mg < data.minimum_mg:
        raise EngineInputError("prescription.taper_input_invalid")

    dose = _mg(data.start_mg)
    step = _mg(data.step_mg)
    floor = _mg(data.minimum_mg)
    days: list[TaperDay] = []
    day_number = 1
    while dose > _ZERO and dose >= floor:
        for _ in range(data.days_per_step):
            if day_number > _MAX_DAYS:
                raise EngineInputError("prescription.taper_too_long")
            days.append(TaperDay(day_number=day_number, dose_mg=dose))
            day_number += 1
        dose = _mg(dose - step)

    schedule = ",".join(format(day.dose_mg, "f") for day in days)
    calculation = CalculationResult(
        code=CODE,
        value=str(len(days)),
        unit="day",
        inputs={
            "start_mg": format(_mg(data.start_mg), "f"),
            "step_mg": format(step, "f"),
            "days_per_step": str(data.days_per_step),
            "minimum_mg": format(floor, "f"),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(Flag(code="schedule_mg", detail={"days": schedule}),),
    )
    return TaperResult(calculation=calculation, days=tuple(days))
