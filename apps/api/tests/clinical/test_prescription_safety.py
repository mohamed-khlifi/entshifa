"""Known answers for the prescription safety checker (ticket P2-08)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ent.engines.prescriptions.safety import (
    VERSION,
    SafetyInput,
    SafetyItem,
    check_safety,
)


def _item(**overrides: object) -> SafetyItem:
    base: dict[str, object] = {
        "allergy_concept_ids": frozenset(),
        "drug_class": "penicillin",
        "is_ototoxic": False,
        "pregnancy_category": None,
        "daily_dose_mg": Decimal("800"),
        "max_daily_dose_mg": Decimal("3000"),
        "is_unstructured": False,
    }
    base.update(overrides)
    return SafetyItem(**base)  # type: ignore[arg-type]


def _codes(data: SafetyInput) -> set[tuple[str, str, int | None]]:
    result = check_safety(data)
    assert VERSION
    return {(alert.code, alert.severity, alert.item_index) for alert in result}


@pytest.mark.clinical
def test_a_known_allergen_blocks_and_a_clear_drug_does_not() -> None:
    blocked = SafetyInput(
        items=(_item(allergy_concept_ids=frozenset({"concept-amox"})),),
        active_allergy_concept_ids=frozenset({"concept-amox"}),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=Decimal("70"),
    )
    assert (
        "prescription.allergy_conflict",
        "block",
        0,
    ) in _codes(blocked)

    clear = SafetyInput(
        items=blocked.items,
        active_allergy_concept_ids=frozenset({"concept-other"}),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=Decimal("70"),
    )
    assert "prescription.allergy_conflict" not in {code for code, _, _ in _codes(clear)}


@pytest.mark.clinical
def test_pediatric_prescription_without_weight_blocks() -> None:
    missing = SafetyInput(
        items=(_item(),),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=True,
        weight_kg=None,
    )
    assert (
        "prescription.pediatric_weight_missing",
        "block",
        None,
    ) in _codes(missing)

    recorded = SafetyInput(
        items=missing.items,
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=True,
        weight_kg=Decimal("18.5"),
    )
    assert "prescription.pediatric_weight_missing" not in {
        code for code, _, _ in _codes(recorded)
    }


@pytest.mark.clinical
def test_dose_equal_to_the_maximum_does_not_block() -> None:
    exact = SafetyInput(
        items=(
            _item(daily_dose_mg=Decimal("3000"), max_daily_dose_mg=Decimal("3000")),
        ),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    assert "prescription.dose_above_maximum" not in {
        code for code, _, _ in _codes(exact)
    }

    over = SafetyInput(
        items=(
            _item(daily_dose_mg=Decimal("3000.001"), max_daily_dose_mg=Decimal("3000")),
        ),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    assert ("prescription.dose_above_maximum", "block", 0) in _codes(over)


@pytest.mark.clinical
def test_ototoxic_warning_requires_hearing_loss_on_the_problem_list() -> None:
    quiet = SafetyInput(
        items=(_item(is_ototoxic=True, drug_class="aminoglycoside"),),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    assert "prescription.ototoxic_with_hearing_loss" not in {
        code for code, _, _ in _codes(quiet)
    }
    listed = SafetyInput(
        items=quiet.items,
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=True,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    assert ("prescription.ototoxic_with_hearing_loss", "warning", 0) in _codes(listed)


@pytest.mark.clinical
def test_duplicate_class_warns_against_current_medication_and_the_same_prescription() -> (
    None
):
    data = SafetyInput(
        items=(
            _item(drug_class="penicillin"),
            _item(drug_class="penicillin"),
            _item(drug_class="  "),
        ),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset({"penicillin"}),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    codes = _codes(data)
    assert ("prescription.duplicate_class", "warning", 0) in codes
    assert ("prescription.duplicate_class", "warning", 1) in codes
    assert ("prescription.duplicate_class", "warning", 2) not in codes


@pytest.mark.clinical
def test_pregnancy_and_breastfeeding_warn_only_for_caution_categories() -> None:
    data = SafetyInput(
        items=(
            _item(pregnancy_category="contraindicated", drug_class="macrolide"),
            _item(pregnancy_category="compatible", drug_class="other"),
            _item(pregnancy_category=None, drug_class="analgesic"),
        ),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=True,
        is_breastfeeding=True,
        is_pediatric=False,
        weight_kg=None,
    )
    codes = _codes(data)
    assert ("prescription.pregnancy_caution", "warning", 0) in codes
    assert ("prescription.breastfeeding_caution", "warning", 0) in codes
    assert ("prescription.pregnancy_caution", "warning", 1) not in codes
    assert ("prescription.pregnancy_caution", "warning", 2) not in codes


@pytest.mark.clinical
def test_a_missing_daily_dose_or_maximum_is_not_an_overdose() -> None:
    data = SafetyInput(
        items=(
            _item(daily_dose_mg=None),
            _item(max_daily_dose_mg=None, drug_class="macrolide"),
        ),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    assert "prescription.dose_above_maximum" not in {
        code for code, _, _ in _codes(data)
    }


@pytest.mark.clinical
def test_non_positive_pediatric_weight_blocks() -> None:
    missing = SafetyInput(
        items=(_item(),),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=True,
        weight_kg=Decimal("0"),
    )
    assert (
        "prescription.pediatric_weight_missing",
        "block",
        None,
    ) in _codes(missing)


@pytest.mark.clinical
def test_caution_category_warns_in_pregnancy() -> None:
    data = SafetyInput(
        items=(_item(pregnancy_category="caution", drug_class="macrolide"),),
        active_allergy_concept_ids=frozenset(),
        active_medication_classes=frozenset(),
        hearing_loss_on_problem_list=False,
        is_pregnant=True,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    assert ("prescription.pregnancy_caution", "warning", 0) in _codes(data)


@pytest.mark.clinical
def test_unstructured_item_skips_drug_checks() -> None:
    data = SafetyInput(
        items=(
            _item(
                is_unstructured=True,
                allergy_concept_ids=frozenset({"concept-amox"}),
                is_ototoxic=True,
                drug_class="penicillin",
            ),
        ),
        active_allergy_concept_ids=frozenset({"concept-amox"}),
        active_medication_classes=frozenset({"penicillin"}),
        hearing_loss_on_problem_list=True,
        is_pregnant=False,
        is_breastfeeding=False,
        is_pediatric=False,
        weight_kg=None,
    )
    codes = {code for code, _, _ in _codes(data)}
    assert codes == {"prescription.unstructured_item"}
