"""Known-answer cases for the Reflux Finding Score.

Belafsky, Postma, Koufman. Laryngoscope 2001;111:1313-1317.
Appendix A: 8 items, total 0-26, above 7 abnormal.
"""

from __future__ import annotations

import pytest

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.laryngoscopy.reflux_finding_score import (
    ABNORMAL_ABOVE,
    ALLOWED,
    CODE,
    TOTAL_MAX,
    VERSION,
    score,
)
from ent.engines.registry import registered_calculators


def _zeros() -> dict[str, int]:
    return {item: 0 for item in ALLOWED}


def _maximum() -> dict[str, int]:
    return {item: max(values) for item, values in ALLOWED.items()}


@pytest.mark.clinical
def test_minimum_is_zero_and_not_abnormal() -> None:
    result = score(items=_zeros())
    assert result.value == "0"
    assert result.code == CODE
    assert result.version == VERSION
    assert result.flags[0].detail["abnormal"] == "false"
    assert result.flags[0].detail["above"] == str(ABNORMAL_ABOVE)


@pytest.mark.clinical
def test_maximum_is_twenty_six() -> None:
    result = score(items=_maximum())
    assert result.value == str(TOTAL_MAX)
    assert result.flags[0].detail["abnormal"] == "true"


@pytest.mark.clinical
def test_seven_is_not_above_the_threshold() -> None:
    items = _zeros()
    items["vocal_fold_edema"] = 3
    items["diffuse_laryngeal_edema"] = 4
    result = score(items=items)
    assert result.value == "7"
    assert result.flags[0].detail["abnormal"] == "false"


@pytest.mark.clinical
def test_eight_is_abnormal() -> None:
    items = _zeros()
    items["vocal_fold_edema"] = 4
    items["diffuse_laryngeal_edema"] = 4
    result = score(items=items)
    assert result.value == "8"
    assert result.flags[0].detail["abnormal"] == "true"


@pytest.mark.clinical
@pytest.mark.parametrize("item", tuple(ALLOWED))
def test_each_item_uses_only_its_published_points(item: str) -> None:
    items = _zeros()
    allowed = max(ALLOWED[item])
    items[item] = allowed
    result = score(items=items)
    assert result.value == str(allowed)
    assert result.inputs[item] == str(allowed)


@pytest.mark.clinical
def test_a_gap_value_is_rejected() -> None:
    items = _zeros()
    items["subglottic_edema"] = 1
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.code == "laryngoscopy.invalid_score"
    assert exc.value.context["item"] == "subglottic_edema"


@pytest.mark.clinical
def test_missing_item_is_not_zero() -> None:
    items = _zeros()
    del items["granuloma"]
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.code == "laryngoscopy.incomplete_score"
    assert exc.value.context["item"] == "granuloma"


@pytest.mark.clinical
def test_bool_and_unknown_item_are_rejected() -> None:
    items = _zeros()
    items["erythema"] = True
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.context["item"] == "erythema"
    items = _zeros()
    items["extra"] = 0
    with pytest.raises(ScoreInputError) as exc:
        score(items=items)
    assert exc.value.context["item"] == "extra"


@pytest.mark.clinical
def test_registry_lists_the_engine() -> None:
    match = [item for item in registered_calculators() if item.code == CODE]
    assert len(match) == 1
    assert match[0].version == VERSION
