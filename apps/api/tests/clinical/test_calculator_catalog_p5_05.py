"""P5-05 calculator catalog known-answer probes."""

from __future__ import annotations

import pytest

from ent.engines.calculator_catalog import evaluate_calculator, registered_calculators
from ent.engines.calculator_errors import CalculatorInputError
from ent.engines.endoscopy.lund_kennedy import CODE as LK_CODE


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
        evaluate_calculator("prescriptions.pediatric_dose", {"weight_kg": "10"})
    assert exc.value.code == "calculator.not_interactive"
