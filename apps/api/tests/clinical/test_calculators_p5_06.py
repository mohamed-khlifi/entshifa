"""P5-06 remaining calculators — known-answer clinical probes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from ent.engines.airway.ett_size import score as ett_score
from ent.engines.airway.myer_cotton import score as myer_cotton_score
from ent.engines.calculator_catalog import evaluate_calculator
from ent.engines.endoscopy.lund_mackay import SINUS_ITEMS
from ent.engines.endoscopy.lund_mackay import score as lund_mackay_score
from ent.engines.general.bmi import score as bmi_score
from ent.engines.general.bsa import score as bsa_score
from ent.engines.general.corrected_age import score as corrected_age_score
from ent.engines.airway.errors import AirwayInputError
from ent.engines.general.errors import GeneralCalculatorInputError
from ent.engines.general.bsa import score as bsa_score
from ent.engines.surgery.errors import SurgeryChecklistInputError
from ent.engines.surgery.adenotonsillectomy import (
    AdenotonsillectomyInput,
    adenotonsillectomy_checklist,
)
from ent.engines.surgery.paradise import ParadiseInput, paradise_checklist
from ent.engines.surgery.tube_criteria import TubeCriteriaInput, tube_criteria_checklist


@pytest.mark.clinical
def test_bmi_reference_case() -> None:
    """70 kg, 170 cm -> BMI 24.22 kg/m2 (normal band)."""
    result = bmi_score(weight_kg=Decimal("70"), height_cm=Decimal("170"))
    assert result.value == "24.22"
    assert any(
        flag.code == "band" and flag.detail["band"] == "normal" for flag in result.flags
    )


@pytest.mark.clinical
def test_bsa_mosteller_reference() -> None:
    """Mosteller (70 kg, 170 cm) ≈ 1.82 m2."""
    result = bsa_score(
        weight_kg=Decimal("70"),
        height_cm=Decimal("170"),
        method="mosteller",
    )
    assert result.value == "1.82"


@pytest.mark.clinical
def test_corrected_age_preterm() -> None:
    """32-week infant at 13 weeks chronological age -> 5.0 corrected weeks."""
    result = corrected_age_score(
        birth_date=date(2024, 1, 1),
        as_of_date=date(2024, 4, 1),
        gestational_age_weeks=32,
        gestational_age_days=0,
    )
    assert result.value == "5.0"


@pytest.mark.clinical
def test_lund_mackay_total() -> None:
    right = dict.fromkeys(SINUS_ITEMS, 0)
    right["ostiomeatal_complex"] = 0
    left = dict.fromkeys(SINUS_ITEMS, 1)
    left["ostiomeatal_complex"] = 2
    result = lund_mackay_score(right=right, left=left)
    assert result.value == "7"
    assert any(
        flag.code == "left_subtotal" and flag.detail["value"] == "7"
        for flag in result.flags
    )


@pytest.mark.clinical
def test_lund_mackay_rejects_invalid_omc() -> None:
    right = dict.fromkeys(SINUS_ITEMS, 0)
    right["ostiomeatal_complex"] = 1
    left = dict.fromkeys(SINUS_ITEMS, 0)
    left["ostiomeatal_complex"] = 0
    with pytest.raises(Exception):
        lund_mackay_score(right=right, left=left)


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("percent", "grade"),
    [(0, "I"), (50, "I"), (51, "II"), (70, "II"), (71, "III"), (100, "IV")],
)
def test_myer_cotton_boundaries(percent: int, grade: str) -> None:
    result = myer_cotton_score(obstruction_percent=percent)
    assert result.value == grade


@pytest.mark.clinical
def test_ett_cuffed_age_six() -> None:
    """6 years cuffed Khine: 6/4 + 3.5 = 5.0 mm."""
    result = ett_score(age_years=Decimal("6"), cuffed=True)
    assert result.value == "5.0"


@pytest.mark.clinical
def test_paradise_criteria_met() -> None:
    data = ParadiseInput(
        episodes_last_year=7,
        episodes_year_2=2,
        episodes_year_3=2,
        fever_38_3c=True,
        cervical_adenopathy=False,
        tonsillar_exudate=False,
        positive_strep_a=False,
        episodes_documented=True,
    )
    assert paradise_checklist(data).value == "met"


@pytest.mark.clinical
def test_tube_recurrent_aom_pathway() -> None:
    data = TubeCriteriaInput(
        aom_episodes_6_months=3,
        aom_episodes_12_months=4,
        middle_ear_effusion_present=True,
        ome_duration_months=0,
        bilateral_ome=False,
        hearing_difficulty_documented=False,
        at_risk_or_symptomatic_ome=False,
    )
    assert tube_criteria_checklist(data).value == "met"


@pytest.mark.clinical
def test_adenotonsillectomy_with_psg() -> None:
    data = AdenotonsillectomyInput(
        sdb_symptoms_present=True,
        tonsil_brodsky_grade=3,
        adenoid_hypertrophy=False,
        psg_performed=True,
        psg_ahi=Decimal("2"),
        age_under_3_years=False,
        high_risk_comorbidity=False,
    )
    result = adenotonsillectomy_checklist(data)
    assert result.value == "met"


@pytest.mark.clinical
def test_pediatric_dose_via_registry() -> None:
    result = evaluate_calculator(
        "prescriptions.pediatric_dose",
        {
            "weight_kg": "10",
            "mg_per_kg_per_day": "80",
            "doses_per_day": "2",
        },
    )
    assert result.value == "400.000"


@pytest.mark.clinical
def test_steroid_taper_via_registry() -> None:
    result = evaluate_calculator(
        "prescriptions.steroid_taper",
        {
            "start_mg": "40",
            "step_mg": "10",
            "days_per_step": "2",
            "minimum_mg": "10",
        },
    )
    assert int(result.value) > 0


@pytest.mark.clinical
def test_bmi_out_of_range_height() -> None:
    with pytest.raises(GeneralCalculatorInputError):
        bmi_score(weight_kg=Decimal("70"), height_cm=Decimal("10"))


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("weight", "height", "band"),
    [
        (Decimal("50"), Decimal("190"), "underweight"),
        (Decimal("90"), Decimal("170"), "overweight"),
        (Decimal("100"), Decimal("170"), "obesity_class_i"),
        (Decimal("120"), Decimal("170"), "obesity_class_iii"),
    ],
)
def test_bmi_severity_bands(weight: Decimal, height: Decimal, band: str) -> None:
    result = bmi_score(weight_kg=weight, height_cm=height)
    assert any(f.code == "band" and f.detail["band"] == band for f in result.flags)


@pytest.mark.clinical
def test_bsa_dubois() -> None:
    result = bsa_score(
        weight_kg=Decimal("70"),
        height_cm=Decimal("170"),
        method="dubois",
    )
    assert result.flags[0].detail["method"] == "dubois"


@pytest.mark.clinical
def test_corrected_age_term_infant() -> None:
    result = corrected_age_score(
        birth_date=date(2024, 1, 1),
        as_of_date=date(2024, 2, 1),
        gestational_age_weeks=40,
        gestational_age_days=0,
    )
    assert result.value == "4.4"


@pytest.mark.clinical
def test_lund_mackay_via_registry() -> None:
    raw = {
        f"right_{item}": 0
        for item in (
            "maxillary",
            "anterior_ethmoid",
            "posterior_ethmoid",
            "sphenoid",
            "frontal",
        )
    }
    raw["right_ostiomeatal_complex"] = 0
    raw.update(
        {
            f"left_{item}": 0
            for item in (
                "maxillary",
                "anterior_ethmoid",
                "posterior_ethmoid",
                "sphenoid",
                "frontal",
            )
        }
    )
    raw["left_ostiomeatal_complex"] = 0
    result = evaluate_calculator("endoscopy.lund_mackay", raw)
    assert result.value == "0"


@pytest.mark.clinical
def test_surgery_errors_validation() -> None:
    from ent.engines.surgery.paradise import ParadiseInput, evaluate_paradise

    with pytest.raises(SurgeryChecklistInputError):
        evaluate_paradise(
            ParadiseInput(
                episodes_last_year=99,
                episodes_year_2=0,
                episodes_year_3=0,
                fever_38_3c=False,
                cervical_adenopathy=False,
                tonsillar_exudate=False,
                positive_strep_a=False,
                episodes_documented=True,
            )
        )


@pytest.mark.clinical
def test_airway_ett_uncuffed() -> None:
    result = ett_score(age_years=Decimal("4"), cuffed=False)
    assert result.flags[0].detail["kind"] == "uncuffed"


@pytest.mark.clinical
def test_airway_input_error() -> None:
    with pytest.raises(AirwayInputError):
        ett_score(age_years=Decimal("0.5"), cuffed=True)
