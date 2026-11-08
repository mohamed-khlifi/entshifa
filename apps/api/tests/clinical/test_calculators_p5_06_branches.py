"""Branch coverage for P5-06 engine modules (clinical gate)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from ent.engines import calculator_catalog as catalog
from ent.engines.airway.errors import AirwayInputError
from ent.engines.airway.ett_size import score as ett_score
from ent.engines.airway.myer_cotton import score as myer_cotton_score
from ent.engines.calculator_errors import CalculatorInputError
from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.endoscopy.lund_mackay import SINUS_ITEMS
from ent.engines.endoscopy.lund_mackay import score as lund_mackay_score
from ent.engines.general.bmi import score as bmi_score
from ent.engines.general.bsa import score as bsa_score
from ent.engines.general.corrected_age import score as corrected_age_score
from ent.engines.general.errors import GeneralCalculatorInputError
from ent.engines.surgery.adenotonsillectomy import (
    AdenotonsillectomyInput,
    adenotonsillectomy_checklist,
    evaluate_adenotonsillectomy,
)
from ent.engines.surgery.errors import SurgeryChecklistInputError
from ent.engines.surgery.paradise import (
    ParadiseInput,
    evaluate_paradise,
    paradise_checklist,
)
from ent.engines.surgery.tube_criteria import TubeCriteriaInput, evaluate_tube_criteria


@pytest.mark.clinical
def test_bmi_weight_out_of_range() -> None:
    with pytest.raises(GeneralCalculatorInputError):
        bmi_score(weight_kg=Decimal("600"), height_cm=Decimal("170"))


@pytest.mark.clinical
def test_bmi_input_not_finite() -> None:
    with pytest.raises(GeneralCalculatorInputError):
        bmi_score(weight_kg=Decimal("NaN"), height_cm=Decimal("170"))


@pytest.mark.clinical
def test_bmi_non_positive_height_meters_guard() -> None:
    class _Height(Decimal):
        def __truediv__(self, other: object) -> Decimal:
            if other == Decimal("100"):
                return Decimal("0")
            return Decimal.__truediv__(self, other)  # type: ignore[arg-type]

    with pytest.raises(GeneralCalculatorInputError):
        bmi_score(weight_kg=Decimal("70"), height_cm=_Height("170"))  # type: ignore[arg-type]


@pytest.mark.clinical
def test_bsa_invalid_inputs() -> None:
    with pytest.raises(GeneralCalculatorInputError):
        bsa_score(
            weight_kg=Decimal("NaN"), height_cm=Decimal("170"), method="mosteller"
        )
    with pytest.raises(GeneralCalculatorInputError):
        bsa_score(weight_kg=Decimal("0"), height_cm=Decimal("170"), method="mosteller")
    with pytest.raises(GeneralCalculatorInputError):
        bsa_score(weight_kg=Decimal("70"), height_cm=Decimal("10"), method="mosteller")
    with pytest.raises(GeneralCalculatorInputError):
        bsa_score(weight_kg=Decimal("70"), height_cm=Decimal("170"), method="invalid")  # type: ignore[arg-type]


@pytest.mark.clinical
def test_bsa_invalid_method_via_registry() -> None:
    with pytest.raises(CalculatorInputError) as exc:
        catalog.evaluate_calculator(
            "general.bsa",
            {"weight_kg": "70", "height_cm": "170", "method": "invalid"},
        )
    assert exc.value.code == "calculator.invalid_select"


@pytest.mark.clinical
def test_corrected_age_validation() -> None:
    with pytest.raises(GeneralCalculatorInputError):
        corrected_age_score(
            birth_date=date(2024, 6, 1),
            as_of_date=date(2024, 1, 1),
            gestational_age_weeks=32,
        )
    with pytest.raises(GeneralCalculatorInputError):
        corrected_age_score(
            birth_date=date(2024, 1, 1),
            as_of_date=date(2024, 4, 1),
            gestational_age_weeks=10,
        )
    with pytest.raises(GeneralCalculatorInputError):
        corrected_age_score(
            birth_date=date(2024, 1, 1),
            as_of_date=date(2024, 4, 1),
            gestational_age_weeks=32,
            gestational_age_days=9,
        )


@pytest.mark.clinical
def test_lund_mackay_missing_item() -> None:
    right = dict.fromkeys(SINUS_ITEMS, 0)
    right["ostiomeatal_complex"] = 0
    left = dict.fromkeys(SINUS_ITEMS, 0)
    del left["maxillary"]
    left["ostiomeatal_complex"] = 0
    with pytest.raises(ScoreInputError):
        lund_mackay_score(right=right, left=left)


@pytest.mark.clinical
def test_lund_mackay_item_out_of_range() -> None:
    right = dict.fromkeys(SINUS_ITEMS, 5)
    right["ostiomeatal_complex"] = 0
    left = dict.fromkeys(SINUS_ITEMS, 0)
    left["ostiomeatal_complex"] = 0
    with pytest.raises(ScoreInputError):
        lund_mackay_score(right=right, left=left)


@pytest.mark.clinical
def test_lund_mackay_missing_omc() -> None:
    right = dict.fromkeys(SINUS_ITEMS, 0)
    left = dict.fromkeys(SINUS_ITEMS, 0)
    left["ostiomeatal_complex"] = 0
    with pytest.raises(ScoreInputError):
        lund_mackay_score(right=right, left=left)


@pytest.mark.clinical
def test_lund_mackay_omc_invalid() -> None:
    right = dict.fromkeys(SINUS_ITEMS, 0)
    right["ostiomeatal_complex"] = 1
    left = dict.fromkeys(SINUS_ITEMS, 0)
    left["ostiomeatal_complex"] = 0
    with pytest.raises(ScoreInputError):
        lund_mackay_score(right=right, left=left)


@pytest.mark.clinical
def test_lund_mackay_total_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ent.engines.endoscopy.lund_mackay.TOTAL_MAX", 1)
    right = dict.fromkeys(SINUS_ITEMS, 0)
    right["maxillary"] = 2
    right["ostiomeatal_complex"] = 0
    left = dict.fromkeys(SINUS_ITEMS, 0)
    left["ostiomeatal_complex"] = 0
    with pytest.raises(ScoreInputError):
        lund_mackay_score(right=right, left=left)


@pytest.mark.clinical
def test_myer_cotton_out_of_range() -> None:
    with pytest.raises(AirwayInputError):
        myer_cotton_score(obstruction_percent=150)


@pytest.mark.clinical
def test_ett_age_invalid_and_out_of_range() -> None:
    with pytest.raises(AirwayInputError):
        ett_score(age_years=Decimal("NaN"), cuffed=True)
    with pytest.raises(AirwayInputError):
        ett_score(age_years=Decimal("17"), cuffed=True)


@pytest.mark.clinical
def test_paradise_two_year_frequency_met() -> None:
    data = ParadiseInput(
        episodes_last_year=2,
        episodes_year_2=5,
        episodes_year_3=1,
        fever_38_3c=True,
        cervical_adenopathy=False,
        tonsillar_exudate=False,
        positive_strep_a=False,
        episodes_documented=True,
    )
    met, flags = evaluate_paradise(data)
    assert met is True
    assert any(
        f.code == "frequency_tier_met" and f.detail["tier"] == "two_year_5_each"
        for f in flags
    )


@pytest.mark.clinical
def test_paradise_not_met_paths() -> None:
    data = ParadiseInput(
        episodes_last_year=2,
        episodes_year_2=1,
        episodes_year_3=1,
        fever_38_3c=False,
        cervical_adenopathy=False,
        tonsillar_exudate=False,
        positive_strep_a=False,
        episodes_documented=True,
    )
    met, _ = evaluate_paradise(data)
    assert met is False
    assert paradise_checklist(data).value == "not_met"


@pytest.mark.clinical
def test_tube_criteria_validation_and_not_met() -> None:
    with pytest.raises(SurgeryChecklistInputError):
        evaluate_tube_criteria(
            TubeCriteriaInput(
                aom_episodes_6_months=0,
                aom_episodes_12_months=0,
                middle_ear_effusion_present=False,
                ome_duration_months=61,
                bilateral_ome=False,
                hearing_difficulty_documented=False,
                at_risk_or_symptomatic_ome=False,
            )
        )
    with pytest.raises(SurgeryChecklistInputError):
        evaluate_tube_criteria(
            TubeCriteriaInput(
                aom_episodes_6_months=99,
                aom_episodes_12_months=0,
                middle_ear_effusion_present=False,
                ome_duration_months=0,
                bilateral_ome=False,
                hearing_difficulty_documented=False,
                at_risk_or_symptomatic_ome=False,
            )
        )
    met, _ = evaluate_tube_criteria(
        TubeCriteriaInput(
            aom_episodes_6_months=0,
            aom_episodes_12_months=0,
            middle_ear_effusion_present=False,
            ome_duration_months=1,
            bilateral_ome=False,
            hearing_difficulty_documented=False,
            at_risk_or_symptomatic_ome=False,
        )
    )
    assert met is False


@pytest.mark.clinical
def test_corrected_age_clamps_negative_days() -> None:
    result = corrected_age_score(
        birth_date=date(2024, 1, 1),
        as_of_date=date(2024, 1, 10),
        gestational_age_weeks=22,
        gestational_age_days=0,
    )
    assert result.value == "0.0"
    assert any(
        f.code == "corrected_days" and f.detail["value"] == "0" for f in result.flags
    )


@pytest.mark.clinical
def test_adenotonsillectomy_psg_required_and_brodsky() -> None:
    with pytest.raises(SurgeryChecklistInputError):
        evaluate_adenotonsillectomy(
            AdenotonsillectomyInput(
                sdb_symptoms_present=True,
                tonsil_brodsky_grade=5,  # brodsky out of range
                adenoid_hypertrophy=False,
                psg_performed=False,
                psg_ahi=None,
                age_under_3_years=False,
                high_risk_comorbidity=False,
            )
        )
    with pytest.raises(SurgeryChecklistInputError):
        evaluate_adenotonsillectomy(
            AdenotonsillectomyInput(
                sdb_symptoms_present=True,
                tonsil_brodsky_grade=3,
                adenoid_hypertrophy=True,
                psg_performed=True,
                psg_ahi=None,
                age_under_3_years=False,
                high_risk_comorbidity=False,
            )
        )
    with pytest.raises(SurgeryChecklistInputError):
        evaluate_adenotonsillectomy(
            AdenotonsillectomyInput(
                sdb_symptoms_present=True,
                tonsil_brodsky_grade=3,
                adenoid_hypertrophy=True,
                psg_performed=True,
                psg_ahi=Decimal("-1"),
                age_under_3_years=False,
                high_risk_comorbidity=False,
            )
        )
    result = adenotonsillectomy_checklist(
        AdenotonsillectomyInput(
            sdb_symptoms_present=True,
            tonsil_brodsky_grade=3,
            adenoid_hypertrophy=True,
            psg_performed=False,
            psg_ahi=None,
            age_under_3_years=True,
            high_risk_comorbidity=False,
        )
    )
    assert result.value == "met"
    assert any(f.code == "adenotonsillectomy_discussion_met" for f in result.flags)

    not_met = adenotonsillectomy_checklist(
        AdenotonsillectomyInput(
            sdb_symptoms_present=False,
            tonsil_brodsky_grade=1,
            adenoid_hypertrophy=False,
            psg_performed=False,
            psg_ahi=None,
            age_under_3_years=False,
            high_risk_comorbidity=False,
        )
    )
    assert not_met.value == "not_met"
    assert not any(f.code == "adenotonsillectomy_discussion_met" for f in not_met.flags)


@pytest.mark.clinical
def test_evaluate_maps_surgery_checklist_input_error() -> None:
    def _boom(_raw: object) -> object:
        raise SurgeryChecklistInputError("surgery.tube_count_out_of_range", field="x")

    spec, _ = catalog._CATALOG["surgery.tube_criteria"]
    catalog._CATALOG["surgery.tube_criteria"] = (spec, _boom)
    try:
        with pytest.raises(CalculatorInputError) as exc:
            catalog.evaluate_calculator("surgery.tube_criteria", {})
        assert exc.value.code == "calculator.clinical_input"
    finally:
        catalog._CATALOG["surgery.tube_criteria"] = (spec, catalog._run_tube_criteria)
