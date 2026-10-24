"""Known-answer audiology calculators (feature spec §8.5, appendix A)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ent.engines.audiology.asymmetry import asymmetry_met
from ent.engines.audiology.asymmetry import score as asymmetry_score
from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.pta import pure_tone_average
from ent.engines.audiology.pta import score as pta_score
from ent.engines.audiology.threshold_shift import significant_shift
from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import AsymmetryRule, ThresholdPoint
from ent.engines.audiology.who_grading import grade_from_pta
from ent.engines.audiology.who_grading import score as who_score
from ent.engines.registry import registered_calculators


def _air(ear: str, hz: int, db: int) -> ThresholdPoint:
    return ThresholdPoint(
        ear=ear,  # type: ignore[arg-type]
        conduction="air",
        frequency_hz=hz,
        level_db=db,
        is_masked=False,
        is_no_response=False,
    )


def _bone(ear: str, hz: int, db: int, masked: bool = True) -> ThresholdPoint:
    return ThresholdPoint(
        ear=ear,  # type: ignore[arg-type]
        conduction="bone",
        frequency_hz=hz,
        level_db=db,
        is_masked=masked,
        is_no_response=False,
    )


def _flat_right(level: int = 15) -> list[ThresholdPoint]:
    return [
        _air("right", 500, level),
        _air("right", 1000, level),
        _air("right", 2000, level),
        _air("right", 4000, level),
    ]


@pytest.mark.clinical
def test_who_four_frequency_pta_normal_below_twenty() -> None:
    """4-frequency mean 15 dB HL -> normal (feature spec: normal is below 20)."""

    thresholds = _flat_right(15)
    result = pta_score(ear="right", formula="4freq_who", thresholds=thresholds)
    assert result.value == "15.00"
    indexed = index_thresholds(thresholds)
    assert (
        grade_from_pta(pure_tone_average(indexed, ear="right", formula="4freq_who"))
        == "normal"
    )
    who = who_score(ear="right", thresholds=thresholds)
    assert who.value == "normal"


@pytest.mark.clinical
def test_pta_twenty_is_mild_who_grade() -> None:
    thresholds = _flat_right(20)
    who = who_score(ear="right", thresholds=thresholds)
    assert who.value == "mild"


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("pta", "grade"),
    [
        (Decimal("19.99"), "normal"),
        (Decimal("20"), "mild"),
        (Decimal("34.99"), "mild"),
        (Decimal("35"), "moderate"),
        (Decimal("49.99"), "moderate"),
        (Decimal("50"), "moderately_severe"),
        (Decimal("64.99"), "moderately_severe"),
        (Decimal("65"), "severe"),
        (Decimal("79.99"), "severe"),
        (Decimal("80"), "profound"),
        (Decimal("94.99"), "profound"),
        (Decimal("95"), "complete"),
    ],
)
def test_who_2021_grade_band_boundaries(pta: Decimal, grade: str) -> None:
    """Feature spec §8.5 / appendix A WHO 2021 boundaries."""

    assert grade_from_pta(pta) == grade


@pytest.mark.clinical
def test_fletcher_uses_two_lowest_of_500_1000_2000() -> None:
    thresholds = [
        _air("left", 500, 40),
        _air("left", 1000, 10),
        _air("left", 2000, 30),
    ]
    indexed = index_thresholds(thresholds)
    pta = pure_tone_average(indexed, ear="left", formula="fletcher")
    assert pta == Decimal("20.00")


@pytest.mark.clinical
def test_no_response_blocks_pta() -> None:
    thresholds = [
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=1000,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
        _air("right", 500, 20),
        _air("right", 2000, 20),
        _air("right", 4000, 20),
    ]
    indexed = index_thresholds(thresholds)
    with pytest.raises(AudiometryInputError):
        pure_tone_average(indexed, ear="right", formula="4freq_who")


@pytest.mark.clinical
def test_asymmetry_default_rule_single_frequency_twenty_db() -> None:
    rule = AsymmetryRule(adjacent_db=15, adjacent_count=2, single_db=20, wrs_percent=15)
    thresholds = [
        _air("right", 1000, 30),
        _air("left", 1000, 5),
    ]
    indexed = index_thresholds(thresholds)
    assert asymmetry_met(indexed, rule=rule)
    result = asymmetry_score(thresholds=thresholds, rule=rule)
    assert result.value == "true"


@pytest.mark.clinical
def test_asha_shift_twenty_db_at_one_frequency() -> None:
    baseline = [_air("right", 2000, 10)]
    current = [_air("right", 2000, 35)]
    assert significant_shift(current, baseline, rule="asha")


@pytest.mark.clinical
def test_registry_lists_audiology_pta() -> None:
    codes = {item.code for item in registered_calculators()}
    assert "audiology.pta" in codes
    assert "audiology.who_grade" in codes
