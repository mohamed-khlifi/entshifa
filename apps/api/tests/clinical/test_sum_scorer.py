"""Known-answer tests for generic questionnaire sum scoring.

Appendix A (feature spec): SNOT-22, NOSE, THI severity bands, MCID examples.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from ent.engines.scoring.errors import (
    IncompleteInstrumentResponseError,
    InstrumentScoreOutOfRangeError,
    InvalidInstrumentAnswerError,
    InvalidInstrumentDefinitionError,
    ScoringEngineError,
)
from ent.engines.scoring.registry import score_from_spec
from ent.engines.scoring.sum_scorer import (
    VERSION,
    _decimal,
    score_questionnaire,
    validate_spec,
)
from ent.engines.scoring.types import (
    InstrumentItemSpec,
    InstrumentScoringSpec,
    SeverityBandSpec,
    SubscaleSpec,
)


def _options_0_to_5() -> tuple[int, ...]:
    return (0, 1, 2, 3, 4, 5)


def _snot_spec() -> InstrumentScoringSpec:
    items = tuple(
        InstrumentItemSpec(
            code=f"q{i}",
            position=i,
            allowed_values=_options_0_to_5(),
        )
        for i in range(1, 23)
    )
    return InstrumentScoringSpec(
        code="snot22",
        version="1.0.0",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("110"),
        reference="SNOT-22; Appendix A",
        items=items,
        scale_multiplier=Decimal("1"),
        mcid=Decimal("8.9"),
    )


def _nose_spec() -> InstrumentScoringSpec:
    items = tuple(
        InstrumentItemSpec(
            code=f"n{i}",
            position=i,
            allowed_values=(0, 1, 2, 3, 4),
            weight=Decimal("5"),
        )
        for i in range(1, 6)
    )
    return InstrumentScoringSpec(
        code="nose",
        version="1.0.0",
        scoring_type="weighted_sum",
        min_score=Decimal("0"),
        max_score=Decimal("100"),
        reference="NOSE; Appendix A",
        items=items,
        scale_multiplier=Decimal("1"),
    )


def _thi_spec() -> InstrumentScoringSpec:
    items = tuple(
        InstrumentItemSpec(
            code=f"t{i}",
            position=i,
            allowed_values=(0, 2, 4),
        )
        for i in range(1, 26)
    )
    bands = (
        SeverityBandSpec("slight", Decimal("0"), Decimal("16")),
        SeverityBandSpec("mild", Decimal("18"), Decimal("36")),
        SeverityBandSpec("moderate", Decimal("38"), Decimal("56")),
        SeverityBandSpec("severe", Decimal("58"), Decimal("76")),
        SeverityBandSpec("catastrophic", Decimal("78"), Decimal("100")),
    )
    return InstrumentScoringSpec(
        code="thi",
        version="1.0.0",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("100"),
        reference="THI; Appendix A",
        items=items,
        severity_bands=bands,
    )


@pytest.mark.clinical
def test_snot22_minimum_and_maximum() -> None:
    spec = _snot_spec()
    validate_spec(spec)
    zero = {f"q{i}": 0 for i in range(1, 23)}
    five = {f"q{i}": 5 for i in range(1, 23)}
    low = score_questionnaire(spec, zero)
    high = score_questionnaire(spec, five)
    assert low.total_score == Decimal("0")
    assert high.total_score == Decimal("110")
    assert low.calculation.version == VERSION


@pytest.mark.clinical
def test_nose_weighted_sum_maximum() -> None:
    spec = _nose_spec()
    answers = {f"n{i}": 4 for i in range(1, 6)}
    result = score_questionnaire(spec, answers)
    assert result.total_score == Decimal("100")


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("answers", "band"),
    [
        ({f"t{i}": 0 for i in range(1, 26)}, "slight"),
        ({f"t{i}": 4 if i <= 9 else 0 for i in range(1, 26)}, "mild"),
        ({f"t{i}": 4 if i <= 14 else 0 for i in range(1, 26)}, "moderate"),
        ({f"t{i}": 4 if i <= 19 else 0 for i in range(1, 26)}, "severe"),
        ({f"t{i}": 4 for i in range(1, 26)}, "catastrophic"),
    ],
)
def test_thi_severity_bands(answers: dict[str, int], band: str) -> None:
    spec = _thi_spec()
    result = score_questionnaire(spec, answers)
    assert result.severity_band == band


@pytest.mark.clinical
def test_reverse_scored_item() -> None:
    spec = InstrumentScoringSpec(
        code="demo",
        version="1.0.0",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("4"),
        reference="unit",
        items=(
            InstrumentItemSpec(
                code="a",
                position=1,
                allowed_values=(0, 1, 2),
                is_reverse_scored=True,
            ),
        ),
    )
    result = score_questionnaire(spec, {"a": 0})
    assert result.total_score == Decimal("2")


@pytest.mark.clinical
def test_incomplete_response_rejected() -> None:
    spec = _snot_spec()
    partial = {f"q{i}": 0 for i in range(1, 22)}
    with pytest.raises(IncompleteInstrumentResponseError):
        score_questionnaire(spec, partial)


@pytest.mark.clinical
def test_invalid_answer_rejected() -> None:
    spec = _snot_spec()
    answers = {f"q{i}": 0 for i in range(1, 23)}
    answers["q1"] = 9
    with pytest.raises(InvalidInstrumentAnswerError):
        score_questionnaire(spec, answers)


@pytest.mark.clinical
def test_mcid_change_from_previous() -> None:
    spec = _snot_spec()
    previous = Decimal("44")
    bumped = {f"q{i}": 5 for i in range(1, 23)}
    second = score_questionnaire(
        spec,
        bumped,
        previous_total_score=previous,
    )
    assert second.change_from_previous is not None
    assert second.mcid_reached is True


@pytest.mark.clinical
def test_invalid_spec_rejected() -> None:
    spec = InstrumentScoringSpec(
        code="bad",
        version="1",
        scoring_type="sum",
        min_score=Decimal("10"),
        max_score=Decimal("0"),
        reference="x",
        items=(
            InstrumentItemSpec(
                code="a",
                position=1,
                allowed_values=(0, 1),
            ),
        ),
    )
    with pytest.raises(InvalidInstrumentDefinitionError):
        validate_spec(spec)


def _minimal_item() -> InstrumentItemSpec:
    return InstrumentItemSpec(
        code="a",
        position=1,
        allowed_values=(0, 1),
    )


def _minimal_spec(
    *,
    max_score: Decimal = Decimal("2"),
    mcid: Decimal | None = None,
) -> InstrumentScoringSpec:
    return InstrumentScoringSpec(
        code="demo",
        version="1.0.0",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=max_score,
        reference="fixture",
        items=(_minimal_item(),),
        mcid=mcid,
    )


@pytest.mark.clinical
def test_score_from_spec_delegates_to_sum_scorer() -> None:
    spec = _nose_spec()
    answers = {f"n{i}": 4 for i in range(1, 6)}
    assert score_from_spec(spec, answers).total_score == Decimal("100")


@pytest.mark.clinical
def test_score_from_spec_rejects_unknown_scoring_type() -> None:
    bad = InstrumentScoringSpec(
        code="demo",
        version="1",
        scoring_type="custom",  # type: ignore[arg-type]
        min_score=Decimal("0"),
        max_score=Decimal("2"),
        reference="x",
        items=(_minimal_item(),),
    )
    with pytest.raises(InvalidInstrumentDefinitionError):
        score_from_spec(bad, {"a": 1})


@pytest.mark.clinical
def test_unknown_answer_key_rejected() -> None:
    spec = _minimal_spec()
    with pytest.raises(InvalidInstrumentAnswerError):
        score_questionnaire(spec, {"a": 0, "extra": 1})


@pytest.mark.clinical
def test_total_out_of_range_rejected() -> None:
    spec = _minimal_spec(max_score=Decimal("0"))  # answer 1 exceeds max
    with pytest.raises(InstrumentScoreOutOfRangeError):
        score_questionnaire(spec, {"a": 1})


@pytest.mark.clinical
@pytest.mark.parametrize(
    "spec",
    [
        InstrumentScoringSpec(
            code="empty",
            version="1",
            scoring_type="sum",
            min_score=Decimal("0"),
            max_score=Decimal("1"),
            reference="x",
            items=(),
        ),
        InstrumentScoringSpec(
            code="mult",
            version="1",
            scoring_type="sum",
            min_score=Decimal("0"),
            max_score=Decimal("1"),
            reference="x",
            items=(_minimal_item(),),
            scale_multiplier=Decimal("0"),
        ),
        InstrumentScoringSpec(
            code="dup",
            version="1",
            scoring_type="sum",
            min_score=Decimal("0"),
            max_score=Decimal("4"),
            reference="x",
            items=(
                _minimal_item(),
                InstrumentItemSpec(code="a", position=2, allowed_values=(0, 1)),
            ),
        ),
        InstrumentScoringSpec(
            code="empty",
            version="1",
            scoring_type="sum",
            min_score=Decimal("0"),
            max_score=Decimal("1"),
            reference="x",
            items=(InstrumentItemSpec(code="a", position=1, allowed_values=()),),
        ),
        InstrumentScoringSpec(
            code="weight",
            version="1",
            scoring_type="weighted_sum",
            min_score=Decimal("0"),
            max_score=Decimal("10"),
            reference="x",
            items=(
                InstrumentItemSpec(
                    code="a",
                    position=1,
                    allowed_values=(0, 1),
                    weight=Decimal("0"),
                ),
            ),
        ),
        InstrumentScoringSpec(
            code="band",
            version="1",
            scoring_type="sum",
            min_score=Decimal("0"),
            max_score=Decimal("10"),
            reference="x",
            items=(_minimal_item(),),
            severity_bands=(SeverityBandSpec("x", Decimal("5"), Decimal("2")),),
        ),
        InstrumentScoringSpec(
            code="sub",
            version="1",
            scoring_type="sum",
            min_score=Decimal("0"),
            max_score=Decimal("10"),
            reference="x",
            items=(_minimal_item(),),
            subscales=(SubscaleSpec("s1", ("missing",)),),
        ),
    ],
)
def test_validate_spec_rejects_invalid_definitions(spec: InstrumentScoringSpec) -> None:
    with pytest.raises(InvalidInstrumentDefinitionError):
        validate_spec(spec)


@pytest.mark.clinical
def test_subscale_totals_from_config_and_item_tags() -> None:
    items = (
        InstrumentItemSpec(code="a", position=1, allowed_values=(0, 1), subscale="tag"),
        InstrumentItemSpec(code="b", position=2, allowed_values=(0, 1)),
    )
    tagged = InstrumentScoringSpec(
        code="tagged",
        version="1",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("4"),
        reference="x",
        items=items,
    )
    tagged_result = score_questionnaire(tagged, {"a": 1, "b": 0})
    assert tagged_result.subscale_scores["tag"] == Decimal("1")

    configured = InstrumentScoringSpec(
        code="configured",
        version="1",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("4"),
        reference="x",
        items=items,
        subscales=(SubscaleSpec("primary", ("a", "b")),),
    )
    cfg_result = score_questionnaire(configured, {"a": 1, "b": 1})
    assert cfg_result.subscale_scores["primary"] == Decimal("2")
    assert any(f.code == "subscale" for f in cfg_result.calculation.flags)


@pytest.mark.clinical
def test_mcid_not_reached_when_below_threshold() -> None:
    spec = _snot_spec()
    answers = {f"q{i}": 0 for i in range(1, 23)}
    answers["q1"] = 1
    result = score_questionnaire(
        spec,
        answers,
        previous_total_score=Decimal("0"),
    )
    assert result.mcid_reached is False


@pytest.mark.clinical
def test_change_without_mcid_leaves_mcid_reached_none() -> None:
    spec = _minimal_spec()
    result = score_questionnaire(
        spec,
        {"a": 1},
        previous_total_score=Decimal("0"),
    )
    assert result.change_from_previous == Decimal("1.00")
    assert result.mcid_reached is None


@pytest.mark.clinical
def test_severity_band_none_when_total_outside_bands() -> None:
    spec = InstrumentScoringSpec(
        code="bands",
        version="1",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("10"),
        reference="x",
        items=(_minimal_item(),),
        severity_bands=(SeverityBandSpec("low", Decimal("5"), Decimal("10")),),
    )
    result = score_questionnaire(spec, {"a": 0})
    assert result.severity_band is None


@pytest.mark.clinical
def test_empty_reference_uses_engine_default() -> None:
    spec = _minimal_spec()
    spec = InstrumentScoringSpec(
        code="demo",
        version="1.0.0",
        scoring_type="sum",
        min_score=Decimal("0"),
        max_score=Decimal("2"),
        reference="",
        items=(_minimal_item(),),
    )
    result = score_questionnaire(spec, {"a": 0})
    assert "questionnaire engine" in result.calculation.reference


@pytest.mark.clinical
def test_decimal_helper_accepts_decimal_instance() -> None:
    value = Decimal("2.50")
    assert _decimal(value) is value


@pytest.mark.clinical
def test_scoring_engine_errors_expose_attributes() -> None:
    incomplete = IncompleteInstrumentResponseError(missing_item_codes=("a",))
    assert incomplete.missing_item_codes == ("a",)
    invalid = InvalidInstrumentAnswerError(item_code="a", value=9)
    assert invalid.item_code == "a"
    out_of_range = InstrumentScoreOutOfRangeError(
        total="5",
        min_score="0",
        max_score="4",
    )
    assert out_of_range.total == "5"
    assert issubclass(ScoringEngineError, Exception)
