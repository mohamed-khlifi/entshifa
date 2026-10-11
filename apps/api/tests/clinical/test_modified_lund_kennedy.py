"""Known-answer cases for modified Lund-Kennedy.

Appendix A: polyps, edema and discharge, 0–2 each side, total 0–12.
Scarring and crusting are not inputs.
# VERIFY: Psaltis et al., Laryngoscope 2014.
"""

from __future__ import annotations

import pytest

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.endoscopy.modified_lund_kennedy import (
    CODE,
    ITEMS,
    SIDE_MAX,
    TOTAL_MAX,
    VERSION,
    score,
)
from ent.engines.endoscopy.ordinal import side_points

_SIDES = ("right", "left")


def _zeros() -> dict[str, int]:
    return {item: 0 for item in ITEMS}


@pytest.mark.clinical
def test_minimum_is_zero() -> None:
    result = score(right=_zeros(), left=_zeros())
    assert result.value == "0"
    assert result.version == VERSION
    assert side_points(result, "right") == 0
    assert side_points(result, "left") == 0


@pytest.mark.clinical
def test_maximum_is_twelve() -> None:
    filled = {item: 2 for item in ITEMS}
    result = score(right=filled, left=filled)
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
    assert result.value == "1"
    assert side_points(result, side) == 1
    assert result.code == CODE


@pytest.mark.clinical
def test_scarring_is_not_an_input() -> None:
    right = _zeros()
    right["scarring"] = 2
    with pytest.raises(ScoreInputError) as exc:
        score(right=right, left=_zeros())
    assert exc.value.code == "endoscopy.invalid_score"
    assert exc.value.context["item"] == "scarring"


@pytest.mark.clinical
def test_missing_discharge_is_incomplete() -> None:
    right = _zeros()
    del right["discharge"]
    with pytest.raises(ScoreInputError) as exc:
        score(right=right, left=_zeros())
    assert exc.value.code == "endoscopy.incomplete_score"
