"""Endotracheal tube internal diameter estimate by age (feature spec §12.6)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ent.engines.airway.errors import AirwayInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "airway.ett_size"
REFERENCE = (
    "Cole F. Pediatric formulas for the anesthetic tube. Anesthesiology 1957;18:687-688. "
    "Khine HH et al. Comparison of cuffed and uncuffed tubes. Anesthesiology 1997;86(3):627-631. "
    "Feature specification §12.6. # VERIFY: local anesthesia protocol."
)
FORMULA = "uncuffed (Cole): age_years/4 + 4; cuffed (Khine): age_years/4 + 3.5; round to 0.5 mm"
_MIN_AGE = Decimal("1")
_MAX_AGE = Decimal("16")
_HALF = Decimal("0.5")


def _round_half_mm(value: Decimal) -> Decimal:
    return (value / _HALF).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * _HALF


def score(*, age_years: Decimal, cuffed: bool = True) -> CalculationResult:
    """Estimate internal diameter for ages 1-16 years."""

    if not age_years.is_finite():
        raise AirwayInputError("airway.ett_age_invalid")
    if age_years < _MIN_AGE or age_years > _MAX_AGE:
        raise AirwayInputError("airway.ett_age_out_of_range")
    offset = Decimal("3.5") if cuffed else Decimal("4")
    raw_id = age_years / Decimal("4") + offset
    rounded = _round_half_mm(raw_id)
    alternate_offset = Decimal("4") if cuffed else Decimal("3.5")
    alternate_raw = age_years / Decimal("4") + alternate_offset
    lip_depth_cm = (rounded * Decimal("3")).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    tube_kind = "cuffed" if cuffed else "uncuffed"
    return CalculationResult(
        code=CODE,
        value=format(rounded, "f"),
        unit="mm",
        inputs={
            "age_years": format(age_years, "f"),
            "cuffed": "true" if cuffed else "false",
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(code="tube_kind", detail={"kind": tube_kind}),
            Flag(code="raw_id_mm", detail={"value": format(raw_id, "f")}),
            Flag(
                code="alternate_id_mm",
                detail={"value": format(_round_half_mm(alternate_raw), "f")},
            ),
            Flag(
                code="lip_depth_cm",
                detail={"value": format(lip_depth_cm, "f"), "unit": "cm"},
            ),
        ),
    )
