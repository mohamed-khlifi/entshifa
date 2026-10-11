"""Shared ordinal side-score. Item meanings are supplied by the caller."""

from __future__ import annotations

from collections.abc import Mapping

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.results import CalculationResult, Flag


def score_ordinal_sides(
    *,
    code: str,
    version: str,
    reference: str,
    formula: str,
    items: tuple[str, ...],
    right: Mapping[str, int],
    left: Mapping[str, int],
    item_max: int,
) -> CalculationResult:
    """Sum explicit integer grades. Missing items are never treated as zero."""

    right_values = _side("right", items, right, item_max)
    left_values = _side("left", items, left, item_max)
    right_total = sum(right_values.values())
    left_total = sum(left_values.values())
    inputs = {
        f"{side}.{item}": str(value)
        for side, values in (("right", right_values), ("left", left_values))
        for item, value in values.items()
    }
    inputs["item_max"] = str(item_max)
    return CalculationResult(
        code=code,
        value=str(right_total + left_total),
        unit="points",
        inputs=inputs,
        formula=formula,
        version=version,
        reference=reference,
        flags=(
            Flag(
                code="side_total",
                detail={"side": "right", "points": str(right_total)},
            ),
            Flag(
                code="side_total",
                detail={"side": "left", "points": str(left_total)},
            ),
        ),
    )


def side_points(result: CalculationResult, side: str) -> int:
    """Read one side total from the engine flags."""

    for flag in result.flags:
        if flag.code == "side_total" and flag.detail.get("side") == side:
            return int(flag.detail["points"])
    raise ScoreInputError(
        "endoscopy.incomplete_score",
        item="side_total",
        side=side,
    )


def _side(
    side: str,
    items: tuple[str, ...],
    values: Mapping[str, int],
    item_max: int,
) -> dict[str, int]:
    required = set(items)
    missing = [item for item in items if item not in values]
    if missing:
        raise ScoreInputError(
            "endoscopy.incomplete_score",
            item=missing[0],
            side=side,
        )
    unexpected = [item for item in values if item not in required]
    if unexpected:
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item=unexpected[0],
            side=side,
        )
    checked: dict[str, int] = {}
    for item in items:
        checked[item] = _grade(values[item], item=item, side=side, item_max=item_max)
    return checked


def _grade(value: int, *, item: str, side: str, item_max: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoreInputError("endoscopy.invalid_score", item=item, side=side)
    if value < 0 or value > item_max:
        raise ScoreInputError("endoscopy.invalid_score", item=item, side=side)
    return value
