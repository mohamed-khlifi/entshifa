"""Scores recompute from observation rows. A missing FEES scale is not a zero."""

from __future__ import annotations

import pytest

from ent.features.laryngoscopy.constants import (
    GRBAS_CONCEPT_CODES,
    PAS_CODE,
    RFS_CONCEPT_CODES,
)
from ent.features.laryngoscopy.exceptions import (
    LaryngoscopyIncompleteScoreError,
    LaryngoscopyInvalidScoreError,
)
from ent.features.laryngoscopy.scoring import ScoreRow, compute


def _rfs(value: int = 0) -> list[ScoreRow]:
    return [
        ScoreRow(concept_code=code, ordinal_value=value)
        for code in RFS_CONCEPT_CODES.values()
    ]


def _grbas(value: int = 1) -> list[ScoreRow]:
    return [
        ScoreRow(concept_code=code, ordinal_value=value)
        for code in GRBAS_CONCEPT_CODES.values()
    ]


def test_empty_exam_records_no_score() -> None:
    scores = compute([], fees_performed=False)
    assert scores.reflux_finding_score is None
    assert scores.grbas is None
    assert scores.penetration_aspiration is None
    assert scores.rfs_score is None
    assert scores.pas_score is None


def test_complete_scores_keep_the_engine_totals() -> None:
    rows = [
        *_rfs(0),
        *_grbas(1),
        ScoreRow(concept_code=PAS_CODE, ordinal_value=2),
    ]
    scores = compute(rows, fees_performed=True)
    assert scores.rfs_score == 0
    assert scores.reflux_finding_score is not None
    assert scores.reflux_finding_score.value == "0"
    assert scores.grbas_g == 1
    assert scores.grbas is not None
    assert scores.grbas.value == "5"
    assert scores.pas_score == 2
    assert scores.penetration_aspiration is not None
    assert scores.penetration_aspiration.flags[0].detail["band"] == "penetration"


def test_fees_without_a_scale_is_incomplete() -> None:
    with pytest.raises(LaryngoscopyIncompleteScoreError):
        compute([], fees_performed=True)


def test_a_scale_without_fees_is_invalid() -> None:
    with pytest.raises(LaryngoscopyInvalidScoreError):
        compute(
            [ScoreRow(concept_code=PAS_CODE, ordinal_value=1)],
            fees_performed=False,
        )


def test_a_partial_reflux_score_is_incomplete() -> None:
    with pytest.raises(LaryngoscopyIncompleteScoreError):
        compute(_rfs(0)[:-1], fees_performed=False)
