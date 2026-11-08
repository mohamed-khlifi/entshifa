"""Myer-Cotton subglottic stenosis grade (feature spec §12.6)."""

from __future__ import annotations

from ent.engines.airway.errors import AirwayInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "airway.myer_cotton"
REFERENCE = (
    "Myer CM 3rd, O'Connor DM, Cotton RT. Ann Otol Rhinol Laryngol "
    "1994;103(4 Pt 1):319-323. Feature specification §12.6; Appendix A."
)
FORMULA = "0-50% grade I; 51-70% grade II; 71-99% grade III; 100% grade IV"


def _grade(percent: int) -> str:
    if percent <= 50:
        return "I"
    if percent <= 70:
        return "II"
    if percent < 100:
        return "III"
    return "IV"


def score(*, obstruction_percent: int) -> CalculationResult:
    """Map obstruction percentage to Myer-Cotton grade I-IV."""

    if obstruction_percent < 0 or obstruction_percent > 100:
        raise AirwayInputError("airway.obstruction_percent_out_of_range")
    grade = _grade(obstruction_percent)
    return CalculationResult(
        code=CODE,
        value=grade,
        unit="grade",
        inputs={"obstruction_percent": str(obstruction_percent)},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(code="grade", detail={"grade": grade}),
            Flag(
                code="obstruction_percent",
                detail={"value": str(obstruction_percent), "unit": "%"},
            ),
        ),
    )
