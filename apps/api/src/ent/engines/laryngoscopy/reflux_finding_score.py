"""Reflux Finding Score.

Eight items. The total is 0–26. A total above 7 is abnormal.
Belafsky PC, Postma GN, Koufman JA. Laryngoscope 2001;111:1313-1317.
# VERIFY: item prose before a signed report narrates a grade. This module
# only accepts the published point values and sums them.
"""

from __future__ import annotations

from collections.abc import Mapping

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "laryngoscopy.reflux_finding_score"
REFERENCE = (
    "Belafsky PC, Postma GN, Koufman JA. Laryngoscope 2001;111:1313-1317. "
    "Appendix A: 8 items, total 0-26, above 7 abnormal."
)
FORMULA = (
    "sum of subglottic edema (0 or 2), ventricular obliteration (0, 2, 4), "
    "erythema (0, 2, 4), vocal fold edema (0-4), diffuse laryngeal edema (0-4), "
    "posterior commissure hypertrophy (0-4), granuloma (0 or 2), "
    "thick endolaryngeal mucus (0 or 2)"
)
ABNORMAL_ABOVE = 7
TOTAL_MAX = 26
ALLOWED: dict[str, frozenset[int]] = {
    "subglottic_edema": frozenset({0, 2}),
    "ventricular_obliteration": frozenset({0, 2, 4}),
    "erythema": frozenset({0, 2, 4}),
    "vocal_fold_edema": frozenset({0, 1, 2, 3, 4}),
    "diffuse_laryngeal_edema": frozenset({0, 1, 2, 3, 4}),
    "posterior_commissure_hypertrophy": frozenset({0, 1, 2, 3, 4}),
    "granuloma": frozenset({0, 2}),
    "thick_endolaryngeal_mucus": frozenset({0, 2}),
}
ITEMS = tuple(ALLOWED)


def score(*, items: Mapping[str, int]) -> CalculationResult:
    """Sum a complete RFS. A missing item is not zero."""

    checked = _items(items)
    total = sum(checked.values())
    abnormal = total > ABNORMAL_ABOVE
    return CalculationResult(
        code=CODE,
        value=str(total),
        unit="points",
        inputs={item: str(value) for item, value in checked.items()},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(
            Flag(
                code="threshold",
                detail={
                    "above": str(ABNORMAL_ABOVE),
                    "abnormal": "true" if abnormal else "false",
                },
            ),
        ),
    )


def _items(items: Mapping[str, int]) -> dict[str, int]:
    missing = [item for item in ITEMS if item not in items]
    if missing:
        raise ScoreInputError(
            "laryngoscopy.incomplete_score",
            item=missing[0],
            side="na",
        )
    unexpected = [item for item in items if item not in ALLOWED]
    if unexpected:
        raise ScoreInputError(
            "laryngoscopy.invalid_score",
            item=unexpected[0],
            side="na",
        )
    checked: dict[str, int] = {}
    for item in ITEMS:
        checked[item] = _points(items[item], item=item)
    return checked


def _points(value: int, *, item: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoreInputError("laryngoscopy.invalid_score", item=item, side="na")
    if value not in ALLOWED[item]:
        raise ScoreInputError("laryngoscopy.invalid_score", item=item, side="na")
    return value
