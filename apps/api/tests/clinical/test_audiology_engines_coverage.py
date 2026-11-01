"""Additional known-answer tests for audiology engine line coverage (§37)."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

import pytest

from ent.engines.audiology.abr import (
    AbrWaveInput,
    compute_abr_metrics,
)
from ent.engines.audiology.abr import (
    score as abr_score,
)
from ent.engines.audiology.air_bone_gap import score as abg_score
from ent.engines.audiology.asymmetry import AsymmetryRule
from ent.engines.audiology.asymmetry import score as asymmetry_score
from ent.engines.audiology.configuration import score as configuration_score
from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.impairment import score_binaural
from ent.engines.audiology.interaural import score as interaural_score
from ent.engines.audiology.loss_type import score as loss_type_score
from ent.engines.audiology.metrics import compute_audiogram_metrics
from ent.engines.audiology.pta import frequencies_for_formula
from ent.engines.audiology.pta import score as pta_score
from ent.engines.audiology.speech_agreement import score as speech_agreement_score
from ent.engines.audiology.threshold_shift import score as shift_score
from ent.engines.audiology.thresholds import index_thresholds, level_db
from ent.engines.audiology.tympanometry import (
    TympanogramInput,
    classify_tympanogram,
)
from ent.engines.audiology.tympanometry import (
    score as tymp_score,
)
from ent.engines.audiology.types import PtaFormula, ShiftRule, ThresholdPoint
from tests.clinical.test_audiology_engines import _air, _bone, _flat_right


def _air_bone_set(
    ear: str,
    air: dict[int, int],
    bone: dict[int, int],
) -> list[ThresholdPoint]:
    points: list[ThresholdPoint] = []
    for hz, db in air.items():
        points.append(_air(ear, hz, db))
    for hz, db in bone.items():
        points.append(_bone(ear, hz, db))
    return points


def _bilateral_air(levels: dict[int, tuple[int, int]]) -> list[ThresholdPoint]:
    points: list[ThresholdPoint] = []
    for hz, (right, left) in levels.items():
        points.append(_air("right", hz, right))
        points.append(_air("left", hz, left))
    return points


@pytest.mark.clinical
def test_abr_invalid_wave_order_raises() -> None:
    with pytest.raises(AudiometryInputError):
        compute_abr_metrics(
            AbrWaveInput(
                wave_i_ms=Decimal("3.00"),
                wave_iii_ms=Decimal("2.00"),
                wave_v_ms=Decimal("5.00"),
            )
        )


@pytest.mark.clinical
def test_abr_interaural_below_threshold_no_flag() -> None:
    metrics = compute_abr_metrics(
        AbrWaveInput(
            wave_i_ms=Decimal("1.50"),
            wave_iii_ms=Decimal("3.80"),
            wave_v_ms=Decimal("5.90"),
        ),
        contralateral_wave_v_ms=Decimal("5.80"),
        threshold_ms=Decimal("0.30"),
    )
    assert metrics.interaural_v_flag is False
    assert metrics.flags == ()


@pytest.mark.clinical
def test_abr_score_registry_wrapper() -> None:
    result = abr_score(
        AbrWaveInput(
            wave_i_ms=Decimal("1.50"),
            wave_iii_ms=Decimal("3.80"),
            wave_v_ms=Decimal("5.90"),
        ),
        contralateral_wave_v_ms=Decimal("5.50"),
    )
    assert result.code == "audiology.abr_latencies"
    assert result.value == "true"


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("compliance", "peak", "expected"),
    [
        (Decimal("0.25"), 0, "As"),
        (Decimal("1.70"), 0, "Ad"),
        (Decimal("0.50"), -150, "C"),
    ],
)
def test_jerger_compliance_variants(
    compliance: Decimal, peak: int, expected: str
) -> None:
    result = classify_tympanogram(
        TympanogramInput(
            ecv_ml=Decimal("1.0"),
            peak_pressure_dapa=peak,
            compliance_ml=compliance,
        )
    )
    assert result.suggested_jerger_type == expected


@pytest.mark.clinical
def test_jerger_type_c_from_peak_only() -> None:
    result = classify_tympanogram(
        TympanogramInput(ecv_ml=None, peak_pressure_dapa=-150, compliance_ml=None)
    )
    assert result.suggested_jerger_type == "C"


@pytest.mark.clinical
def test_threshold_shift_consecutive_nr_resets_before_third() -> None:
    baseline = [
        _air("right", 500, 10),
        _air("right", 1000, 10),
        _air("right", 2000, 10),
        _air("right", 4000, 10),
    ]
    current = [
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=500,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=1000,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
        _air("right", 2000, 10),
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=4000,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
    ]
    result = shift_score(
        current=current, baseline=baseline, rule=cast(ShiftRule, "asha")
    )
    assert result.value == "false"


@pytest.mark.clinical
def test_tympanogram_score_covers_compliance_branch() -> None:
    result = tymp_score(
        TympanogramInput(
            ecv_ml=Decimal("1.0"),
            peak_pressure_dapa=0,
            compliance_ml=Decimal("0.80"),
        )
    )
    assert result.value == "A"
    result = tymp_score(
        TympanogramInput(
            ecv_ml=Decimal("1.0"),
            peak_pressure_dapa=-150,
            compliance_ml=Decimal("0.10"),
        )
    )
    assert result.value == "B"


@pytest.mark.clinical
def test_air_bone_gap_score() -> None:
    thresholds = _air_bone_set(
        "right",
        {500: 30, 1000: 30, 2000: 30, 4000: 30},
        {500: 10, 1000: 10, 2000: 10, 4000: 10},
    )
    result = abg_score(thresholds=thresholds, ear="right")
    assert result.value == "20.00"


@pytest.mark.clinical
def test_interaural_score() -> None:
    thresholds = _bilateral_air(
        {500: (20, 30), 1000: (20, 25), 2000: (20, 20), 4000: (20, 20)}
    )
    result = interaural_score(thresholds=thresholds, pta_formula="4freq_who")
    assert result.value != ""


@pytest.mark.clinical
def test_threshold_shift_occupational_and_score() -> None:
    baseline = [
        _air("right", 2000, 10),
        _air("right", 3000, 10),
        _air("right", 4000, 10),
    ]
    current = [
        _air("right", 2000, 25),
        _air("right", 3000, 25),
        _air("right", 4000, 25),
    ]
    result = shift_score(
        current=current, baseline=baseline, rule=cast(ShiftRule, "occupational")
    )
    assert result.value == "true"


@pytest.mark.clinical
def test_threshold_shift_adjacent_ten_db_asha() -> None:
    baseline = [
        _air("right", 500, 10),
        _air("right", 1000, 10),
        _air("right", 2000, 10),
        _air("right", 4000, 10),
    ]
    current = [
        _air("right", 500, 25),
        _air("right", 1000, 25),
        _air("right", 2000, 10),
        _air("right", 4000, 10),
    ]
    result = shift_score(
        current=current, baseline=baseline, rule=cast(ShiftRule, "asha")
    )
    assert result.value == "true"


@pytest.mark.clinical
def test_pta_high_freq_and_invalid_formula() -> None:
    thresholds = [
        _air("right", 2000, 20),
        _air("right", 4000, 30),
        _air("right", 8000, 40),
    ]
    result = pta_score(thresholds=thresholds, ear="right", formula="high_freq")
    assert result.value == "30.00"
    with pytest.raises(AudiometryInputError):
        frequencies_for_formula(cast(PtaFormula, "invalid"))


@pytest.mark.clinical
def test_speech_agreement_score() -> None:
    thresholds = _flat_right(20)
    agree = speech_agreement_score(
        thresholds=thresholds, ear="right", srt_db=22, pta_formula="4freq_who"
    )
    assert agree.value == "false"
    disagree = speech_agreement_score(
        thresholds=thresholds, ear="right", srt_db=40, pta_formula="4freq_who"
    )
    assert disagree.value == "true"


@pytest.mark.clinical
def test_loss_type_conductive_and_mixed() -> None:
    conductive = _air_bone_set(
        "right",
        {500: 40, 1000: 40, 2000: 40, 4000: 40},
        {500: 10, 1000: 10, 2000: 10, 4000: 10},
    )
    assert loss_type_score(thresholds=conductive, ear="right").value == "conductive"
    mixed = _air_bone_set(
        "right",
        {500: 50, 1000: 50, 2000: 50, 4000: 50},
        {500: 30, 1000: 30, 2000: 30, 4000: 30},
    )
    assert loss_type_score(thresholds=mixed, ear="right").value == "mixed"


@pytest.mark.clinical
def test_configuration_patterns_and_score() -> None:
    notched = [
        _air("right", 500, 10),
        _air("right", 1000, 10),
        _air("right", 2000, 10),
        _air("right", 4000, 35),
        _air("right", 8000, 10),
    ]
    assert configuration_score(thresholds=notched, ear="right").value == "notched"
    sloping = [
        _air("right", 500, 10),
        _air("right", 1000, 15),
        _air("right", 2000, 20),
        _air("right", 4000, 40),
        _air("right", 6000, 50),
        _air("right", 8000, 55),
    ]
    assert configuration_score(thresholds=sloping, ear="right").value == "sloping"


@pytest.mark.clinical
def test_impairment_score_binaural() -> None:
    left_points = [_air("left", hz, 50) for hz in (500, 1000, 2000, 4000)]
    thresholds = _flat_right(40) + left_points
    result = score_binaural(thresholds=thresholds)
    assert result.value != ""


@pytest.mark.clinical
def test_asymmetry_adjacent_pair_and_wrs() -> None:
    rule = AsymmetryRule(adjacent_db=15, adjacent_count=2, single_db=25, wrs_percent=15)
    thresholds = _bilateral_air(
        {
            500: (10, 30),
            1000: (10, 30),
            2000: (10, 10),
            4000: (10, 10),
        }
    )
    result = asymmetry_score(
        thresholds=thresholds,
        rule=rule,
        speech_right=80,
        speech_left=50,
    )
    assert result.value == "true"


@pytest.mark.clinical
def test_threshold_indexing_masked_and_invalid() -> None:
    unmasked = _air("right", 1000, 20)
    masked = _bone("right", 1000, 15, masked=True)
    indexed = index_thresholds([unmasked, masked])
    assert indexed[("right", "bone", 1000)].level_db == 15
    with pytest.raises(AudiometryInputError):
        index_thresholds(
            [
                ThresholdPoint(
                    ear="invalid",
                    conduction="air",
                    frequency_hz=1000,
                    level_db=20,
                    is_masked=False,
                    is_no_response=False,
                )
            ]
        )


@pytest.mark.clinical
def test_level_db_no_response_and_missing_level() -> None:
    indexed = index_thresholds(
        [
            ThresholdPoint(
                ear="right",
                conduction="air",
                frequency_hz=1000,
                level_db=120,
                is_masked=False,
                is_no_response=True,
            )
        ]
    )
    with pytest.raises(AudiometryInputError):
        level_db(indexed, ear="right", conduction="air", frequency_hz=1000)
    assert (
        level_db(
            indexed,
            ear="right",
            conduction="air",
            frequency_hz=1000,
            allow_no_response=True,
        )
        == 120
    )
    indexed_none = index_thresholds(
        [
            ThresholdPoint(
                ear="right",
                conduction="air",
                frequency_hz=2000,
                level_db=None,
                is_masked=False,
                is_no_response=False,
            )
        ]
    )
    with pytest.raises(AudiometryInputError):
        level_db(indexed_none, ear="right", conduction="air", frequency_hz=2000)


@pytest.mark.clinical
def test_abr_interval_when_earlier_wave_missing() -> None:
    metrics = compute_abr_metrics(
        AbrWaveInput(wave_i_ms=None, wave_iii_ms=Decimal("3.00"), wave_v_ms=None)
    )
    assert metrics.i_iii_ms is None
    metrics = compute_abr_metrics(
        AbrWaveInput(wave_i_ms=Decimal("1.50"), wave_iii_ms=None, wave_v_ms=None)
    )
    assert metrics.i_iii_ms is None
    assert metrics.interaural_v_diff_ms is None


@pytest.mark.clinical
def test_jerger_type_b_without_large_ecv() -> None:
    result = classify_tympanogram(
        TympanogramInput(
            ecv_ml=Decimal("1.0"),
            peak_pressure_dapa=0,
            compliance_ml=Decimal("0.10"),
        )
    )
    assert result.suggested_jerger_type == "B"
    assert result.large_canal_volume_flag is False


@pytest.mark.clinical
def test_configuration_rising_cookie_corner_precipitous() -> None:
    rising = [
        _air("right", 500, 50),
        _air("right", 1000, 45),
        _air("right", 2000, 20),
        _air("right", 4000, 15),
        _air("right", 6000, 10),
        _air("right", 8000, 5),
    ]
    assert configuration_score(thresholds=rising, ear="right").value == "rising"
    cookie = [
        _air("right", 500, 10),
        _air("right", 1000, 15),
        _air("right", 2000, 35),
        _air("right", 4000, 40),
        _air("right", 6000, 10),
        _air("right", 8000, 5),
    ]
    assert configuration_score(thresholds=cookie, ear="right").value == "cookie_bite"
    sloping_tail = [
        _air("right", 500, 20),
        _air("right", 1000, 25),
        _air("right", 2000, 30),
        _air("right", 4000, 35),
        _air("right", 6000, 30),
        _air("right", 8000, 28),
    ]
    assert configuration_score(thresholds=sloping_tail, ear="right").value == "sloping"
    flat_fallback = [
        _air("right", 500, 24),
        _air("right", 1000, 26),
        _air("right", 2000, 28),
        _air("right", 4000, 30),
        _air("right", 6000, 20),
        _air("right", 8000, 19),
    ]
    assert configuration_score(thresholds=flat_fallback, ear="right").value == "flat"


@pytest.mark.clinical
def test_threshold_shift_worsening_helper() -> None:
    from ent.engines.audiology.threshold_shift import _worsening

    assert _worsening(15, 10) == 5
    assert _worsening(None, 10) is None
    baseline = [_air("right", 2000, 10)]
    current = [_air("right", 2000, 30)]
    result = shift_score(
        current=current,
        baseline=baseline,
        rule=cast(ShiftRule, "occupational"),
    )
    assert result.value == "false"


@pytest.mark.clinical
def test_index_thresholds_keeps_masked_when_unmasked_arrives_second() -> None:
    points = [
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=1000,
            level_db=15,
            is_masked=True,
            is_no_response=False,
        ),
        _air("right", 1000, 25),
    ]
    indexed = index_thresholds(points)
    assert indexed[("right", "air", 1000)].level_db == 15
    assert indexed[("right", "air", 1000)].is_masked is True


@pytest.mark.clinical
def test_metrics_empty_thresholds_and_optional_paths() -> None:
    rule = AsymmetryRule(adjacent_db=15, adjacent_count=2, single_db=20, wrs_percent=15)
    with pytest.raises(AudiometryInputError):
        compute_audiogram_metrics(
            thresholds=[],
            pta_formula="4freq_who",
            asymmetry_rule=rule,
            shift_rule=cast(ShiftRule, "asha"),
        )
    sparse = [_air("right", 1000, 20)]
    metrics = compute_audiogram_metrics(
        thresholds=sparse,
        pta_formula="4freq_who",
        asymmetry_rule=rule,
        shift_rule=cast(ShiftRule, "asha"),
    )
    assert metrics.pta_right is None


@pytest.mark.clinical
def test_loss_type_sensorineural_when_no_abg() -> None:
    thresholds = [
        _air("right", 500, 45),
        _air("right", 1000, 45),
        _air("right", 2000, 45),
        _air("right", 4000, 45),
    ]
    assert loss_type_score(thresholds=thresholds, ear="right").value == "sensorineural"


@pytest.mark.clinical
def test_threshold_shift_consecutive_no_response() -> None:
    baseline = [
        _air("right", 500, 10),
        _air("right", 1000, 10),
        _air("right", 2000, 10),
        _air("right", 4000, 10),
    ]
    current = [
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=500,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=1000,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=2000,
            level_db=120,
            is_masked=False,
            is_no_response=True,
        ),
        _air("right", 4000, 10),
    ]
    result = shift_score(
        current=current, baseline=baseline, rule=cast(ShiftRule, "asha")
    )
    assert result.value == "true"


@pytest.mark.clinical
def test_threshold_shift_not_met() -> None:
    baseline = [_air("right", 2000, 10)]
    current = [_air("right", 2000, 15)]
    result = shift_score(
        current=current, baseline=baseline, rule=cast(ShiftRule, "asha")
    )
    assert result.value == "false"


@pytest.mark.clinical
def test_interaural_score_when_pta_unavailable() -> None:
    result = interaural_score(
        thresholds=[_air("right", 1000, 20), _air("left", 1000, 30)],
        pta_formula="4freq_who",
    )
    assert result.value == ""


@pytest.mark.clinical
def test_pta_three_frequency_formula() -> None:
    thresholds = [
        _air("right", 500, 10),
        _air("right", 1000, 20),
        _air("right", 2000, 30),
    ]
    result = pta_score(thresholds=thresholds, ear="right", formula="3freq")
    assert result.value == "20.00"


@pytest.mark.clinical
def test_speech_agreement_when_pta_missing() -> None:
    result = speech_agreement_score(
        thresholds=[_air("right", 1000, 20)],
        ear="right",
        srt_db=30,
        pta_formula="4freq_who",
    )
    assert result.value == "false"


@pytest.mark.clinical
def test_index_thresholds_masked_over_unmasked_air() -> None:
    points = [
        _air("right", 1000, 30),
        ThresholdPoint(
            ear="right",
            conduction="air",
            frequency_hz=1000,
            level_db=20,
            is_masked=True,
            is_no_response=False,
        ),
    ]
    indexed = index_thresholds(points)
    assert indexed[("right", "air", 1000)].level_db == 20
    assert indexed[("right", "air", 1000)].is_masked is True


@pytest.mark.clinical
def test_compute_audiogram_metrics_with_baseline_and_speech() -> None:
    from ent.engines.audiology.types import SpeechEarInput

    left = [_air("left", hz, 20) for hz in (500, 1000, 2000, 4000)]
    current = _flat_right(35) + left
    baseline = _flat_right(10)
    rule = AsymmetryRule(adjacent_db=15, adjacent_count=2, single_db=20, wrs_percent=15)
    metrics = compute_audiogram_metrics(
        thresholds=current,
        pta_formula="4freq_who",
        asymmetry_rule=rule,
        shift_rule=cast(ShiftRule, "asha"),
        baseline_thresholds=baseline,
        speech_right=SpeechEarInput(srt_db=35, wrs_percent=90),
    )
    assert metrics.shift_flag is True
