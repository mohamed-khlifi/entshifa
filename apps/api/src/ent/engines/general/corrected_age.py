"""Corrected age for infants born preterm (feature spec §12.5)."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ent.engines.general.errors import GeneralCalculatorInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "general.corrected_age"
REFERENCE = (
    "AAP Committee on Fetus and Newborn. Pediatrics 2004;114(5):1362-1364. "
    "Feature specification §12.5."
)
FORMULA = "corrected_days = chronological_days - max(0, (40*7) - gestational_age_days_at_birth)"
TERM_GESTATION_DAYS = 40 * 7
_WEEK_PRECISION = Decimal("0.1")


def _validate_gestational(weeks: int, days: int) -> int:
    if weeks < 22 or weeks > 42:
        raise GeneralCalculatorInputError("general.gestational_weeks_out_of_range")
    if days < 0 or days > 6:
        raise GeneralCalculatorInputError("general.gestational_days_out_of_range")
    return weeks * 7 + days


def score(
    *,
    birth_date: date,
    as_of_date: date,
    gestational_age_weeks: int,
    gestational_age_days: int = 0,
) -> CalculationResult:
    """Compute corrected age in weeks. Gestational age is at birth."""

    if as_of_date < birth_date:
        raise GeneralCalculatorInputError("general.as_of_before_birth")
    ga_at_birth = _validate_gestational(gestational_age_weeks, gestational_age_days)
    chronological_days = (as_of_date - birth_date).days
    prematurity_days = max(0, TERM_GESTATION_DAYS - ga_at_birth)
    corrected_days = chronological_days - prematurity_days
    if corrected_days < 0:
        corrected_days = 0
    corrected_weeks = (Decimal(corrected_days) / Decimal("7")).quantize(
        _WEEK_PRECISION, rounding=ROUND_HALF_UP
    )
    corrected_months = (Decimal(corrected_days) / Decimal("30.4375")).quantize(
        _WEEK_PRECISION, rounding=ROUND_HALF_UP
    )
    return CalculationResult(
        code=CODE,
        value=format(corrected_weeks, "f"),
        unit="weeks",
        inputs={
            "birth_date": birth_date.isoformat(),
            "as_of_date": as_of_date.isoformat(),
            "gestational_age_weeks": str(gestational_age_weeks),
            "gestational_age_days": str(gestational_age_days),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(
                code="chronological_days",
                detail={"value": str(chronological_days)},
            ),
            Flag(
                code="prematurity_days",
                detail={"value": str(prematurity_days)},
            ),
            Flag(code="corrected_days", detail={"value": str(corrected_days)}),
            Flag(
                code="corrected_months_approx",
                detail={"value": format(corrected_months, "f"), "unit": "months"},
            ),
        ),
    )
