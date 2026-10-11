"""Lund-Kennedy endoscopic score.

Five items on each side, each an explicit integer 0, 1 or 2. The total is 0–20.
# VERIFY: item 0/1/2 prose against Lund & Kennedy 1995 before any narrative uses it.
This module only checks the range and sums the stored grades.
"""

from __future__ import annotations

from collections.abc import Mapping

from ent.engines.endoscopy.ordinal import score_ordinal_sides
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "endoscopy.lund_kennedy"
REFERENCE = (
    "Lund VJ, Kennedy DW. Ann Otol Rhinol Laryngol Suppl 1995;167:17-21. Appendix A."
)
FORMULA = (
    "right+left; each side is polyps+edema+discharge+scarring+crusting; "
    "each item is an integer 0-2"
)
ITEMS = ("polyps", "edema", "discharge", "scarring", "crusting")
ITEM_MAX = 2
SIDE_MAX = 10
TOTAL_MAX = 20


def score(
    *,
    right: Mapping[str, int],
    left: Mapping[str, int],
) -> CalculationResult:
    """Sum a complete Lund-Kennedy pair. Does not infer grades from findings."""

    return score_ordinal_sides(
        code=CODE,
        version=VERSION,
        reference=REFERENCE,
        formula=FORMULA,
        items=ITEMS,
        right=right,
        left=left,
        item_max=ITEM_MAX,
    )
