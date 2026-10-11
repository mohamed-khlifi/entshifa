"""Modified Lund-Kennedy endoscopic score.

Polyps, edema and discharge on each side, each an explicit integer 0, 1 or 2.
The total is 0–12. Scarring and crusting are not part of this score.
# VERIFY: bibliographic details against Psaltis et al., Laryngoscope 2014.
"""

from __future__ import annotations

from collections.abc import Mapping

from ent.engines.endoscopy.ordinal import score_ordinal_sides
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "endoscopy.modified_lund_kennedy"
REFERENCE = (
    "Psaltis AJ, Li G, Vaezeafshar R, Cho KS, Hwang PH. "
    "Laryngoscope 2014;124:2216-2223. Appendix A."
)
FORMULA = "right+left; each side is polyps+edema+discharge; each item is an integer 0-2"
ITEMS = ("polyps", "edema", "discharge")
ITEM_MAX = 2
SIDE_MAX = 6
TOTAL_MAX = 12


def score(
    *,
    right: Mapping[str, int],
    left: Mapping[str, int],
) -> CalculationResult:
    """Sum a complete modified Lund-Kennedy pair."""

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
