"""Scores recompute from observation rows, not from a second copy of the form."""

from __future__ import annotations

from decimal import Decimal

from ent.features.endoscopy.constants import (
    ADENOID_CODE,
    LK_CONCEPT_CODES,
    POLYP_GRADE_CODE,
)
from ent.features.endoscopy.scoring import ScoreRow, compute


def _lk(side: str, item: str, grade: int) -> ScoreRow:
    return ScoreRow(LK_CONCEPT_CODES[item], side, grade, None)


def _complete(polyp_right: int, scarring_right: int) -> list[ScoreRow]:
    rows: list[ScoreRow] = []
    for side in ("right", "left"):
        for item in LK_CONCEPT_CODES:
            grade = scarring_right if item == "scarring" and side == "right" else 0
            if item == "polyps" and side == "right":
                grade = polyp_right
            rows.append(_lk(side, item, grade))
    return rows


def test_scarring_counts_for_lund_kennedy_only() -> None:
    scores = compute(_complete(polyp_right=0, scarring_right=2), polyp_scale="meltzer")
    assert scores.lund_kennedy.value == "2"
    assert scores.lund_kennedy_right == 2
    assert scores.lund_kennedy_left == 0
    assert scores.modified_lund_kennedy.value == "0"
    assert scores.polyp_grade is None
    assert scores.adenoid is None


def test_polyp_grade_names_the_scale_and_adenoid_is_a_percentage() -> None:
    rows = _complete(polyp_right=1, scarring_right=0)
    rows.append(ScoreRow(POLYP_GRADE_CODE, "right", 4, None))
    rows.append(ScoreRow(POLYP_GRADE_CODE, "left", 0, None))
    rows.append(ScoreRow(ADENOID_CODE, "midline", None, Decimal("25")))
    scores = compute(rows, polyp_scale="meltzer")
    assert scores.lund_kennedy.value == "1"
    assert scores.modified_lund_kennedy.value == "1"
    assert scores.polyp_grade is not None
    assert scores.polyp_grade.value == "4/0"
    assert scores.polyp_grade.inputs["scale"] == "meltzer"
    assert scores.adenoid is not None
    assert scores.adenoid.value == "25"
    assert scores.adenoid_obstruction_pct == 25


def test_one_polyp_side_is_incomplete() -> None:
    from ent.features.endoscopy.exceptions import EndoscopyIncompleteScoreError

    rows = _complete(polyp_right=0, scarring_right=0)
    rows.append(ScoreRow(POLYP_GRADE_CODE, "right", 1, None))
    try:
        compute(rows, polyp_scale="lildholdt")
    except EndoscopyIncompleteScoreError as exc:
        assert exc.context["item"] == "polyp_grade"
        assert exc.context["side"] == "left"
    else:
        raise AssertionError("expected an incomplete polyp grade")
