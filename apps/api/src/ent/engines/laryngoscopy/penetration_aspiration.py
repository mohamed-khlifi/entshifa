"""Penetration-Aspiration Scale.

An integer 1–8. 1 is no entry, 2–5 penetration, 6–8 aspiration.
Rosenbek JC et al. Dysphagia 1996;11:93-98. Appendix A states 1 to 8.
# VERIFY: the 2-5 and 6-8 band labels against Rosenbek 1996 before narrative use.
"""

from __future__ import annotations

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "laryngoscopy.penetration_aspiration"
REFERENCE = "Rosenbek JC et al. Dysphagia 1996;11:93-98. Appendix A: 1 to 8."
FORMULA = "integer 1-8; 1 none, 2-5 penetration, 6-8 aspiration"
MINIMUM = 1
MAXIMUM = 8


def score(*, level: int) -> CalculationResult:
    """Record one PAS level. Does not infer the level from residue."""

    checked = _level(level)
    if checked == 1:
        band = "none"
    elif checked <= 5:
        band = "penetration"
    else:
        band = "aspiration"
    return CalculationResult(
        code=CODE,
        value=str(checked),
        unit="grade",
        inputs={"level": str(checked)},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(Flag(code="band", detail={"band": band}),),
    )


def _level(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoreInputError(
            "laryngoscopy.invalid_score",
            item="pas",
            side="na",
        )
    if value < MINIMUM or value > MAXIMUM:
        raise ScoreInputError(
            "laryngoscopy.invalid_score",
            item="pas",
            side="na",
        )
    return value
