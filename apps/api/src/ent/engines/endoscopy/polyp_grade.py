"""Overall polyp grade on the clinic's named scale.

Meltzer is 0–4 per side. Lildholdt is 0–3 per side. This is not the
Lund-Kennedy polyp item, which stays 0–2.
# VERIFY: grade prose for Meltzer and Lildholdt. Appendix A names the ranges only.
"""

from __future__ import annotations

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "endoscopy.polyp_grade"
REFERENCE = "Appendix A. Meltzer grade 0-4 or Lildholdt grade 0-3."
FORMULA = "per-side grade on the named scale; meltzer 0-4, lildholdt 0-3"
SCALE_MAX = {"meltzer": 4, "lildholdt": 3}


def score(*, scale: str, right: int, left: int) -> CalculationResult:
    """Record both sides. The value names the grades; the scale is an input."""

    if scale not in SCALE_MAX:
        raise ScoreInputError("endoscopy.invalid_score", item="scale", side="na")
    maximum = SCALE_MAX[scale]
    right_grade = _grade(right, side="right", maximum=maximum)
    left_grade = _grade(left, side="left", maximum=maximum)
    return CalculationResult(
        code=CODE,
        value=f"{right_grade}/{left_grade}",
        unit="grade",
        inputs={
            "scale": scale,
            "right": str(right_grade),
            "left": str(left_grade),
            "max_grade": str(maximum),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(
                code="side_grade",
                detail={"side": "right", "grade": str(right_grade)},
            ),
            Flag(
                code="side_grade",
                detail={"side": "left", "grade": str(left_grade)},
            ),
        ),
    )


def _grade(value: int, *, side: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoreInputError("endoscopy.invalid_score", item="polyp_grade", side=side)
    if value < 0 or value > maximum:
        raise ScoreInputError("endoscopy.invalid_score", item="polyp_grade", side=side)
    return value
