"""Adenoid size as a percentage of choanal obstruction.

# VERIFY: no 4-grade band is defined in the feature specification.
Only the integer percentage 0–100 is stored.
"""

from __future__ import annotations

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "endoscopy.adenoid_obstruction"
REFERENCE = "Feature specification section 7. Choanal obstruction percentage."
FORMULA = "integer percentage of choanal obstruction from 0 to 100"
MINIMUM = 0
MAXIMUM = 100


def score(*, percent: int) -> CalculationResult:
    """Accept an explicit percentage. Does not assign a grade band."""

    if isinstance(percent, bool) or not isinstance(percent, int):
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item="adenoid_obstruction_pct",
            side="midline",
        )
    if percent < MINIMUM or percent > MAXIMUM:
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item="adenoid_obstruction_pct",
            side="midline",
        )
    return CalculationResult(
        code=CODE,
        value=str(percent),
        unit="%",
        inputs={"percent": str(percent)},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
