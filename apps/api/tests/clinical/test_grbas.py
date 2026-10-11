"""Known-answer cases for GRBAS.

Hirano M. Clinical Examination of Voice. Springer, 1981.
Appendix A: grade, roughness, breathiness, asthenia, strain, 0 to 3 each.
"""

from __future__ import annotations

import pytest

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.laryngoscopy.grbas import (
    CODE,
    ITEMS,
    TOTAL_MAX,
    VERSION,
    score,
)
from ent.engines.registry import registered_calculators


def _zeros() -> dict[str, int]:
    return {item: 0 for item in ITEMS}


@pytest.mark.clinical
def test_minimum_is_zero() -> None:
    result = score(items=_zeros())
    assert result.value == "0"
    assert result.code == CODE
    assert result.version == VERSION


@pytest.mark.clinical
def test_maximum_is_fifteen() -> None:
    result = score(items={item: 3 for item in ITEMS})
    assert result.value == str(TOTAL_MAX)


@pytest.mark.clinical
@pytest.mark.parametrize("item", ITEMS)
def test_each_component_adds_one(item: str) -> None:
    items = _zeros()
    items[item] = 1
    result = score(items=items)
    assert result.value == "1"
    assert result.inputs[item] == "1"


@pytest.mark.clinical
@pytest.mark.parametrize("value", [-1, 4, True])
def test_out_of_range_component_is_rejected(value: int) -> None:
    items = _zeros()
    items["breathiness"] = value
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.code == "laryngoscopy.invalid_score"
    assert exc.value.context["item"] == "breathiness"


@pytest.mark.clinical
def test_missing_component_is_not_zero() -> None:
    items = _zeros()
    del items["strain"]
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.code == "laryngoscopy.incomplete_score"
    assert exc.value.context["item"] == "strain"


@pytest.mark.clinical
def test_unknown_component_is_rejected() -> None:
    items = _zeros()
    items["pitch"] = 1
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.context["item"] == "pitch"


@pytest.mark.clinical
def test_registry_lists_the_engine() -> None:
    match = [item for item in registered_calculators() if item.code == CODE]
    assert len(match) == 1
    assert match[0].version == VERSION
