"""Known-answer cases for adenoid obstruction percentage.

Section 7 stores a percentage of choanal obstruction. No grade band is applied.
"""

from __future__ import annotations

import pytest

from ent.engines.endoscopy.adenoid import CODE, MAXIMUM, MINIMUM, VERSION, score
from ent.engines.endoscopy.errors import ScoreInputError


@pytest.mark.clinical
@pytest.mark.parametrize("percent", [MINIMUM, 50, MAXIMUM])
def test_percentage_is_stored_as_given(percent: int) -> None:
    result = score(percent=percent)
    assert result.code == CODE
    assert result.version == VERSION
    assert result.value == str(percent)
    assert result.unit == "%"
    assert result.inputs["percent"] == str(percent)


@pytest.mark.clinical
@pytest.mark.parametrize("percent", [-1, 101, True])
def test_percentage_outside_0_to_100_is_rejected(percent: int) -> None:
    with pytest.raises(ScoreInputError) as exc:
        score(percent=percent)
    assert exc.value.code == "endoscopy.invalid_score"
    assert exc.value.context["item"] == "adenoid_obstruction_pct"
