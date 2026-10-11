"""Known-answer cases for overall polyp grade.

Appendix A: Meltzer 0–4 or Lildholdt 0–3. The scale name is part of the result.
# VERIFY: grade prose. These tests cover the ranges only.
"""

from __future__ import annotations

import pytest

from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.endoscopy.polyp_grade import CODE, VERSION, score


@pytest.mark.clinical
def test_meltzer_minimum_and_maximum() -> None:
    result = score(scale="meltzer", right=0, left=4)
    assert result.code == CODE
    assert result.version == VERSION
    assert result.value == "0/4"
    assert result.inputs["scale"] == "meltzer"
    assert result.inputs["max_grade"] == "4"
    assert result.reference
    assert "Meltzer" in result.reference or "meltzer" in result.formula


@pytest.mark.clinical
def test_lildholdt_maximum() -> None:
    result = score(scale="lildholdt", right=3, left=0)
    assert result.value == "3/0"
    assert result.inputs["scale"] == "lildholdt"
    assert result.inputs["max_grade"] == "3"


@pytest.mark.clinical
def test_meltzer_rejects_five() -> None:
    with pytest.raises(ScoreInputError) as exc:
        score(scale="meltzer", right=5, left=0)
    assert exc.value.code == "endoscopy.invalid_score"


@pytest.mark.clinical
def test_lildholdt_rejects_meltzer_maximum() -> None:
    with pytest.raises(ScoreInputError) as exc:
        score(scale="lildholdt", right=4, left=0)
    assert exc.value.code == "endoscopy.invalid_score"
    assert exc.value.context["side"] == "right"


@pytest.mark.clinical
def test_unknown_scale_is_rejected() -> None:
    with pytest.raises(ScoreInputError) as exc:
        score(scale="lund_kennedy", right=0, left=0)
    assert exc.value.context["item"] == "scale"


@pytest.mark.clinical
def test_bool_is_not_a_grade() -> None:
    with pytest.raises(ScoreInputError):
        score(scale="meltzer", right=True, left=0)
