"""P5-05 calculator catalog known-answer probes."""

from __future__ import annotations

import pytest

from ent.engines.calculator_catalog import (
    evaluate_calculator,
    get_calculator_spec,
    registered_calculators,
)
from ent.engines.calculator_errors import CalculatorInputError
from ent.engines.endoscopy.lund_kennedy import CODE as LK_CODE
from ent.engines.laryngoscopy.reflux_finding_score import ITEMS as RFS_ITEMS


@pytest.mark.clinical
def test_interactive_registry_lists_phase3_and_phase4() -> None:
    codes = {spec.code for spec in registered_calculators() if spec.interactive}
    for code in (
        LK_CODE,
        "endoscopy.modified_lund_kennedy",
        "laryngoscopy.reflux_finding_score",
        "audiology.pta",
        "audiology.configuration",
        "audiology.jerger_tympanogram",
    ):
        assert code in codes


@pytest.mark.clinical
def test_lund_kennedy_reference_sum_literature_case() -> None:
    """Lund & Kennedy 1995: each item 0–2, five items per side, total 0–20."""
    raw = {
        "right_polyps": 1,
        "right_edema": 1,
        "right_discharge": 0,
        "right_scarring": 0,
        "right_crusting": 0,
        "left_polyps": 2,
        "left_edema": 1,
        "left_discharge": 1,
        "left_scarring": 0,
        "left_crusting": 1,
    }
    result = evaluate_calculator(LK_CODE, raw)
    assert result.value == "7"
    assert result.version
    assert result.reference


@pytest.mark.clinical
def test_pta_three_frequency_mean() -> None:
    """PTA 3-freq = mean(500, 1000, 2000) dB HL (feature spec §8.5)."""
    raw = {
        "ear": "right",
        "pta_formula": "3freq",
        "air_right_500": 20,
        "air_right_1000": 30,
        "air_right_2000": 40,
    }
    result = evaluate_calculator("audiology.pta", raw)
    assert result.value == "30.00"
    assert result.unit == "dB HL"


@pytest.mark.clinical
def test_non_interactive_engine_rejected() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator("scoring.questionnaire_sum", {"weight_kg": "10"})
    assert exc.value.code == "calculator.not_interactive"


@pytest.mark.clinical
def test_get_calculator_spec_unknown() -> None:
    assert get_calculator_spec("missing.calculator") is None


@pytest.mark.clinical
def test_evaluate_unknown_code() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator("missing.calculator", {})
    assert exc.value.code == "calculator.not_found"


@pytest.mark.clinical
def test_pta_invalid_formula() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator(
            "audiology.pta",
            {"ear": "right", "pta_formula": "invalid", "air_right_500": 20},
        )
    assert exc.value.code == "calculator.invalid_select"


@pytest.mark.clinical
def test_pta_four_frequency_who_sparse_grid() -> None:
    """Exercise WHO-frequency fallback when the sparse matrix omits 250/6000/8000."""
    raw = {
        "ear": "right",
        "pta_formula": "4freq_who",
        "air_right_500": 20,
        "air_right_1000": 30,
        "air_right_2000": 40,
        "air_right_4000": 50,
    }
    result = evaluate_calculator("audiology.pta", raw)
    assert result.value


@pytest.mark.clinical
def test_pta_high_frequency_formula() -> None:
    from ent.engines.audiology.types import PTA_HIGH_FREQUENCIES_HZ

    raw = {"ear": "left", "pta_formula": "high_freq"}
    for hz in PTA_HIGH_FREQUENCIES_HZ:
        raw[f"air_left_{hz}"] = 25
    result = evaluate_calculator("audiology.pta", raw)
    assert result.unit == "dB HL"


@pytest.mark.clinical
def test_pta_high_frequency_empty_grid_exercises_fallback_freqs() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator(
            "audiology.pta",
            {"ear": "right", "pta_formula": "high_freq"},
        )
    assert exc.value.code == "calculator.clinical_input"


@pytest.mark.clinical
def test_pta_who_formula_empty_grid_exercises_fallback_freqs() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator(
            "audiology.pta",
            {"ear": "right", "pta_formula": "4freq_who"},
        )
    assert exc.value.code == "calculator.clinical_input"


@pytest.mark.clinical
def test_rfs_disallowed_ordinal() -> None:
    raw = {item: 0 for item in RFS_ITEMS}
    raw["subglottic_edema"] = 1
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator("laryngoscopy.reflux_finding_score", raw)
    assert exc.value.code == "calculator.out_of_range"


@pytest.mark.clinical
def test_pta_missing_thresholds_wraps_clinical_error() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        evaluate_calculator("audiology.pta", {"ear": "right", "pta_formula": "3freq"})
    assert exc.value.code == "calculator.clinical_input"


@pytest.mark.clinical
def test_pta_fletcher_formula_sparse_grid() -> None:
    raw = {
        "ear": "right",
        "pta_formula": "fletcher",
        "air_right_500": 20,
        "air_right_1000": 25,
        "air_right_2000": 30,
    }
    result = evaluate_calculator("audiology.pta", raw)
    assert result.value
