"""Known-answer cases for the Penetration-Aspiration Scale.

Rosenbek JC et al. Dysphagia 1996;11:93-98.
Appendix A: 1 to 8.
# VERIFY: band labels (none, penetration, aspiration) against that paper.
"""

from __future__ import annotations

import pytest

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.laryngoscopy.penetration_aspiration import (
    CODE,
    VERSION,
    score,
)
from ent.engines.registry import registered_calculators


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("level", "band"),
    [
        (1, "none"),
        (2, "penetration"),
        (5, "penetration"),
        (6, "aspiration"),
        (8, "aspiration"),
    ],
)
def test_published_bands(level: int, band: str) -> None:
    result = score(level=level)
    assert result.value == str(level)
    assert result.code == CODE
    assert result.version == VERSION
    assert result.flags[0].detail["band"] == band


@pytest.mark.clinical
@pytest.mark.parametrize("level", [0, 9, True])
def test_out_of_range_level_is_rejected(level: int) -> None:
    with pytest.raises(ScoreInputError) as exc:
        score(level=level)
    assert exc.value.code == "laryngoscopy.invalid_score"
    assert exc.value.context["item"] == "pas"


@pytest.mark.clinical
def test_registry_lists_the_engine() -> None:
    match = [item for item in registered_calculators() if item.code == CODE]
    assert len(match) == 1
    assert match[0].version == VERSION
