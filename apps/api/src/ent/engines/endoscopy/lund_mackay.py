"""Lund-Mackay CT staging (feature spec §12.4 and Appendix A)."""

from __future__ import annotations

from collections.abc import Mapping

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "endoscopy.lund_mackay"
REFERENCE = (
    "Lund VJ, Mackay IS. Rhinology 1993;31(4):183-184. "
    "Feature specification §12.4; Appendix A (0-24)."
)
FORMULA = (
    "per side: maxillary, anterior_ethmoid, posterior_ethmoid, "
    "sphenoid, frontal (0-2 each) + ostiomeatal_complex (0 or 2); total 0-24"
)
SINUS_ITEMS = (
    "maxillary",
    "anterior_ethmoid",
    "posterior_ethmoid",
    "sphenoid",
    "frontal",
)
TOTAL_MAX = 24
SINUS_MAX = 2
OMC_ALLOWED = frozenset({0, 2})


def _side_value(side: str, mapping: Mapping[str, int]) -> tuple[int, dict[str, str]]:
    inputs: dict[str, str] = {}
    total = 0
    for item in SINUS_ITEMS:
        if item not in mapping:
            raise ScoreInputError("endoscopy.lund_mackay_missing_item", field=item)
        value = mapping[item]
        if not isinstance(value, int) or value < 0 or value > SINUS_MAX:
            raise ScoreInputError(
                "endoscopy.lund_mackay_item_out_of_range",
                field=item,
            )
        key = f"{side}_{item}"
        inputs[key] = str(value)
        total += value
    if "ostiomeatal_complex" not in mapping:
        raise ScoreInputError(
            "endoscopy.lund_mackay_missing_item",
            field="ostiomeatal_complex",
        )
    omc = mapping["ostiomeatal_complex"]
    if omc not in OMC_ALLOWED:
        raise ScoreInputError(
            "endoscopy.lund_mackay_omc_invalid",
            field="ostiomeatal_complex",
        )
    omc_key = f"{side}_ostiomeatal_complex"
    inputs[omc_key] = str(omc)
    total += omc
    return total, inputs


def score(
    *,
    right: Mapping[str, int],
    left: Mapping[str, int],
) -> CalculationResult:
    """Sum a complete Lund-Mackay CT form. Missing fields are not zero."""

    right_total, right_inputs = _side_value("right", right)
    left_total, left_inputs = _side_value("left", left)
    total = right_total + left_total
    if total > TOTAL_MAX:
        raise ScoreInputError("endoscopy.lund_mackay_total_out_of_range")
    inputs = {**right_inputs, **left_inputs}
    return CalculationResult(
        code=CODE,
        value=str(total),
        unit="points",
        inputs=inputs,
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(code="right_subtotal", detail={"value": str(right_total)}),
            Flag(code="left_subtotal", detail={"value": str(left_total)}),
        ),
    )
