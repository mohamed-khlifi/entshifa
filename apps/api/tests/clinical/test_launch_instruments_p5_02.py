"""Known-answer tests for P5-02 launch questionnaire instruments."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ent.engines.scoring.errors import (
    IncompleteInstrumentResponseError,
    InvalidInstrumentAnswerError,
)
from ent.engines.scoring.registry import score_from_spec
from ent.engines.scoring.sum_scorer import score_questionnaire, validate_spec
from ent.seeds.instruments_launch_specs import LAUNCH_INSTRUMENT_SPECS
from ent.seeds.instruments_option_labels import option_values_for_scale
from ent.seeds.instruments_scoring import (
    engine_scoring_spec_from_launch,
    launch_spec_by_code,
)


def _answers_all(spec_code: str, value: int) -> dict[str, int]:
    launch = launch_spec_by_code(spec_code)
    return {item.code: value for item in launch.items}


def _min_value(spec_code: str) -> int:
    launch = launch_spec_by_code(spec_code)
    return min(option_values_for_scale(launch.scale_key))


def _max_value(spec_code: str) -> int:
    launch = launch_spec_by_code(spec_code)
    return max(option_values_for_scale(launch.scale_key))


@pytest.mark.clinical
@pytest.mark.parametrize("spec_code", [s.code for s in LAUNCH_INSTRUMENT_SPECS])
def test_launch_instrument_min_and_max_scores(spec_code: str) -> None:
    launch = launch_spec_by_code(spec_code)
    spec = engine_scoring_spec_from_launch(launch)
    validate_spec(spec)
    lo = _min_value(spec_code)
    hi = _max_value(spec_code)
    low = score_questionnaire(spec, _answers_all(spec_code, lo))
    high = score_questionnaire(spec, _answers_all(spec_code, hi))
    assert low.total_score == Decimal(str(launch.min_score))
    assert high.total_score == Decimal(str(launch.max_score))


@pytest.mark.clinical
def test_snot22_mcid_from_previous() -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code("snot22"))
    baseline = score_questionnaire(spec, _answers_all("snot22", 2))
    bumped = score_questionnaire(
        spec,
        _answers_all("snot22", 5),
        previous_total_score=baseline.total_score,
    )
    assert bumped.mcid_reached is True


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("spec_code", "answers", "band"),
    [
        ("thi", _answers_all("thi", 0), "slight"),
        (
            "thi",
            {**_answers_all("thi", 0), **{f"t{i}": 4 for i in range(1, 10)}},
            "mild",
        ),
        (
            "thi",
            {**_answers_all("thi", 0), **{f"t{i}": 4 for i in range(1, 15)}},
            "moderate",
        ),
        (
            "thi",
            {**_answers_all("thi", 0), **{f"t{i}": 4 for i in range(1, 20)}},
            "severe",
        ),
        ("thi", _answers_all("thi", 4), "catastrophic"),
        ("dhi", _answers_all("dhi", 0), "none"),
        ("vhi10", _answers_all("vhi10", 0), "normal"),
        ("vhi10", _answers_all("vhi10", 4), "abnormal"),
        ("rsi", _answers_all("rsi", 0), "normal"),
        ("rsi", _answers_all("rsi", 5), "abnormal"),
        ("eat10", _answers_all("eat10", 0), "normal"),
        (
            "eat10",
            {**_answers_all("eat10", 0), "e1": 1, "e2": 1, "e3": 1},
            "abnormal",
        ),
        ("epworth", _answers_all("epworth", 0), "normal"),
        ("epworth", _answers_all("epworth", 3), "severe"),
        ("stopbang", _answers_all("stopbang", 0), "low"),
        (
            "stopbang",
            {**_answers_all("stopbang", 0), **{f"sb{i}": 1 for i in range(1, 6)}},
            "high",
        ),
        ("osa18", _answers_all("osa18", 1), "mild"),
        ("osa18", _answers_all("osa18", 7), "severe"),
    ],
)
def test_launch_severity_bands(
    spec_code: str, answers: dict[str, int], band: str
) -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code(spec_code))
    result = score_questionnaire(spec, answers)
    assert result.severity_band == band


@pytest.mark.clinical
def test_dhi_subscales_at_maximum() -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code("dhi"))
    result = score_questionnaire(spec, _answers_all("dhi", 4))
    assert result.subscale_scores["physical"] == Decimal("28.00")
    assert result.subscale_scores["emotional"] == Decimal("36.00")
    assert result.subscale_scores["functional"] == Decimal("36.00")


@pytest.mark.clinical
def test_nose_multiplier_matches_appendix_a() -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code("nose"))
    result = score_questionnaire(spec, _answers_all("nose", 4))
    assert result.total_score == Decimal("100.00")


@pytest.mark.clinical
@pytest.mark.parametrize("spec_code", [s.code for s in LAUNCH_INSTRUMENT_SPECS])
def test_incomplete_launch_response_rejected(spec_code: str) -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code(spec_code))
    answers = _answers_all(spec_code, _min_value(spec_code))
    first_key = next(iter(answers))
    del answers[first_key]
    with pytest.raises(IncompleteInstrumentResponseError):
        score_questionnaire(spec, answers)


@pytest.mark.clinical
def test_thi_rejects_invalid_option_value() -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code("thi"))
    answers = _answers_all("thi", 0)
    answers["t1"] = 1
    with pytest.raises(InvalidInstrumentAnswerError):
        score_questionnaire(spec, answers)


@pytest.mark.clinical
def test_osa18_rejects_zero_answer() -> None:
    spec = engine_scoring_spec_from_launch(launch_spec_by_code("osa18"))
    answers = _answers_all("osa18", 2)
    answers["osa1"] = 0
    with pytest.raises(InvalidInstrumentAnswerError):
        score_questionnaire(spec, answers)


@pytest.mark.clinical
def test_all_launch_specs_validate_and_score_via_registry() -> None:
    for launch in LAUNCH_INSTRUMENT_SPECS:
        spec = engine_scoring_spec_from_launch(launch)
        validate_spec(spec)
        lo = _min_value(launch.code)
        output = score_from_spec(spec, _answers_all(launch.code, lo))
        assert output.total_score == Decimal(str(launch.min_score))
