"""GRBAS perceptual voice grade.

Grade, roughness, breathiness, asthenia and strain, each an integer 0–3.
Hirano M. Clinical Examination of Voice. Springer, 1981. Appendix A.
# VERIFY: descriptor prose for 0/1/2/3 before a report narrates a component.
"""

from __future__ import annotations

from collections.abc import Mapping

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "laryngoscopy.grbas"
REFERENCE = "Hirano M. Clinical Examination of Voice. Springer, 1981. Appendix A."
FORMULA = "G+R+B+A+S; each component is an integer 0-3"
ITEMS = ("grade", "roughness", "breathiness", "asthenia", "strain")
ITEM_MAX = 3
TOTAL_MAX = 15


def score(*, items: Mapping[str, int]) -> CalculationResult:
    """Sum a complete GRBAS. A missing component is not zero."""

    checked = _items(items)
    return CalculationResult(
        code=CODE,
        value=str(sum(checked.values())),
        unit="points",
        inputs={item: str(value) for item, value in checked.items()},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )


def _items(items: Mapping[str, int]) -> dict[str, int]:
    missing = [item for item in ITEMS if item not in items]
    if missing:
        raise ScoreInputError(
            "laryngoscopy.incomplete_score",
            item=missing[0],
            side="na",
        )
    unexpected = [item for item in items if item not in ITEMS]
    if unexpected:
        raise ScoreInputError(
            "laryngoscopy.invalid_score",
            item=unexpected[0],
            side="na",
        )
    return {item: _grade(items[item], item=item) for item in ITEMS}


def _grade(value: int, *, item: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoreInputError("laryngoscopy.invalid_score", item=item, side="na")
    if value < 0 or value > ITEM_MAX:
        raise ScoreInputError("laryngoscopy.invalid_score", item=item, side="na")
    return value
