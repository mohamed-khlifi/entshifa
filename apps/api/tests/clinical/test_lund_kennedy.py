"""Known-answer cases for the Lund-Kennedy endoscopic score.

Appendix A: five items, 0–2 each side, total 0–20.
# VERIFY: item 0/1/2 prose against Lund & Kennedy 1995. These tests only sum grades.
"""

from __future__ import annotations

import pytest

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.endoscopy.lund_kennedy import (
    CODE,
    ITEMS,
    SIDE_MAX,
    TOTAL_MAX,
    VERSION,
    score,
)
from ent.engines.endoscopy.ordinal import side_points
from ent.engines.registry import registered_calculators

_SIDES = ("right", "left")


def _zeros() -> dict[str, int]:
    return {item: 0 for item in ITEMS}


def _pair(value: int) -> tuple[dict[str, int], dict[str, int]]:
    return ({item: value for item in ITEMS}, {item: value for item in ITEMS})


@pytest.mark.clinical
def test_minimum_is_zero() -> None:
    right, left = _pair(0)
    result = score(right=right, left=left)
    assert result.value == "0"
    assert result.code == CODE
    assert result.version == VERSION
    assert side_points(result, "right") == 0
    assert side_points(result, "left") == 0


@pytest.mark.clinical
def test_maximum_is_twenty() -> None:
    right, left = _pair(2)
    result = score(right=right, left=left)
    assert result.value == str(TOTAL_MAX)
    assert side_points(result, "right") == SIDE_MAX
    assert side_points(result, "left") == SIDE_MAX


@pytest.mark.clinical
@pytest.mark.parametrize("item", ITEMS)
@pytest.mark.parametrize("side", _SIDES)
def test_each_item_adds_one(item: str, side: str) -> None:
    right = _zeros()
    left = _zeros()
    target = right if side == "right" else left
    target[item] = 1
    result = score(right=right, left=left)
    other = "left" if side == "right" else "right"
    assert result.value == "1"
    assert side_points(result, side) == 1
    assert side_points(result, other) == 0
    assert result.inputs[f"{side}.{item}"] == "1"


@pytest.mark.clinical
def test_missing_item_is_not_zero() -> None:
    right = _zeros()
    del right["polyps"]
    with pytest.raises(ScoreInputError) as exc:
        score(right=right, left=_zeros())
    assert exc.value.code == "endoscopy.incomplete_score"
    assert exc.value.context["item"] == "polyps"
    assert exc.value.context["side"] == "right"


@pytest.mark.clinical
@pytest.mark.parametrize("value", [3, -1, True])
def test_out_of_range_item_is_rejected(value: int) -> None:
    right = _zeros()
    right["edema"] = value
    with pytest.raises(ScoreInputError) as exc:
        score(right=right, left=_zeros())
    assert exc.value.code == "endoscopy.invalid_score"
    assert exc.value.context["item"] == "edema"


@pytest.mark.clinical
def test_registry_lists_the_engine() -> None:
    match = [item for item in registered_calculators() if item.code == CODE]
    assert len(match) == 1
    assert match[0].version == VERSION
