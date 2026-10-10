"""Weight-based dose from a formulary rule supplied by the caller.

The numbers (mg/kg/day, maximum, doses per day, age caps, concentration)
are inputs. This module does not contain a drug's dose.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.prescriptions.errors import EngineInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
REFERENCE = (
    "mg/day = weight_kg * formulary mg_per_kg_per_day; "
    "mg/dose = mg/day / doses_per_day; "
    "mL/dose = mg/dose / concentration_mg_per_ml. "
    "Rules are caller inputs (formulary_entry). Architecture 25.11."
)
CODE = "prescriptions.pediatric_dose"
FORMULA = (
    "mg_per_day = weight_kg * mg_per_kg_per_day; "
    "mg_per_dose = mg_per_day / doses_per_day; "
    "ml_per_dose = mg_per_dose / concentration_mg_per_ml"
)

_MG = Decimal("0.001")
_ML = Decimal("0.01")
_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class AgeCap:
    """A maximum daily dose that applies up to a completed age. Both are inputs."""

    max_completed_years: int
    max_mg_per_day: Decimal


@dataclass(frozen=True, slots=True)
class DosingRule:
    """Resolved rule after the service picked an indication. Not a drug table."""

    mg_per_kg_per_day: Decimal
    doses_per_day: int
    max_mg_per_day: Decimal | None = None
    indication_code: str | None = None


@dataclass(frozen=True, slots=True)
class PediatricDoseInput:
    weight_kg: Decimal
    rule: DosingRule
    concentration_mg_per_ml: Decimal | None = None
    completed_years: int | None = None
    age_caps: tuple[AgeCap, ...] = ()


def _mg(value: Decimal) -> Decimal:
    return value.quantize(_MG, rounding=ROUND_HALF_UP)


def _ml(value: Decimal) -> Decimal:
    return value.quantize(_ML, rounding=ROUND_HALF_UP)


def _require_positive(value: Decimal, code: str) -> None:
    if not value.is_finite() or value <= _ZERO:
        raise EngineInputError(code)


def applicable_max_mg_per_day(data: PediatricDoseInput) -> Decimal | None:
    """The tighter of the rule maximum and the narrowest covering age cap."""

    age_max: Decimal | None = None
    if data.age_caps:
        if data.completed_years is None:
            raise EngineInputError("prescription.dosing_age_required")
        if data.completed_years < 0:
            raise EngineInputError("prescription.dosing_age_invalid")
        covering = [
            cap
            for cap in data.age_caps
            if data.completed_years <= cap.max_completed_years
        ]
        if covering:
            chosen = min(covering, key=lambda cap: cap.max_completed_years)
            _require_positive(chosen.max_mg_per_day, "prescription.dosing_max_invalid")
            age_max = chosen.max_mg_per_day
    rule_max = data.rule.max_mg_per_day
    if rule_max is not None:
        _require_positive(rule_max, "prescription.dosing_max_invalid")
    if age_max is None:
        return rule_max
    if rule_max is None:
        return age_max
    return min(rule_max, age_max)


def weight_based_dose(data: PediatricDoseInput) -> CalculationResult:
    """Apply a formulary mg/kg/day rule. Does not substitute the maximum."""

    _require_positive(data.weight_kg, "prescription.dosing_weight_invalid")
    _require_positive(data.rule.mg_per_kg_per_day, "prescription.dosing_rule_invalid")
    if data.rule.doses_per_day < 1:
        raise EngineInputError("prescription.dosing_frequency_invalid")
    for cap in data.age_caps:
        if cap.max_completed_years < 0:
            raise EngineInputError("prescription.dosing_age_invalid")

    daily = _mg(data.weight_kg * data.rule.mg_per_kg_per_day)
    per_dose = _mg(daily / Decimal(data.rule.doses_per_day))
    maximum = applicable_max_mg_per_day(data)

    flags: list[Flag] = [
        Flag(
            code="mg_per_day",
            detail={"value": format(daily, "f"), "unit": "mg"},
        ),
        Flag(
            code="mg_per_kg_per_day_rule",
            detail={
                "value": format(data.rule.mg_per_kg_per_day, "f"),
                "unit": "mg/kg/day",
            },
        ),
        Flag(
            code="doses_per_day",
            detail={"value": str(data.rule.doses_per_day)},
        ),
    ]
    volume: Decimal | None = None
    if data.concentration_mg_per_ml is None:
        flags.append(Flag(code="volume_unavailable", detail={}))
    else:
        _require_positive(
            data.concentration_mg_per_ml,
            "prescription.dosing_concentration_invalid",
        )
        volume = _ml(per_dose / data.concentration_mg_per_ml)
        flags.append(
            Flag(
                code="volume_ml",
                detail={"value": format(volume, "f"), "unit": "mL"},
            )
        )
    if maximum is not None and daily > maximum:
        flags.append(
            Flag(
                code="dose_above_maximum",
                detail={
                    "daily_mg": format(daily, "f"),
                    "max_mg_per_day": format(_mg(maximum), "f"),
                },
            )
        )

    inputs = {
        "weight_kg": format(data.weight_kg, "f"),
        "mg_per_kg_per_day": format(data.rule.mg_per_kg_per_day, "f"),
        "doses_per_day": str(data.rule.doses_per_day),
        "max_mg_per_day": "" if maximum is None else format(maximum, "f"),
        "concentration_mg_per_ml": (
            ""
            if data.concentration_mg_per_ml is None
            else format(data.concentration_mg_per_ml, "f")
        ),
        "completed_years": (
            "" if data.completed_years is None else str(data.completed_years)
        ),
        "indication_code": data.rule.indication_code or "",
    }
    return CalculationResult(
        code=CODE,
        value=format(per_dose, "f"),
        unit="mg",
        inputs=inputs,
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=tuple(flags),
    )
