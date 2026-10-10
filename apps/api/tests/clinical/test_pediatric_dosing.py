"""Known-answer cases for weight-based dosing.

The rule is the architecture section 25.11 example
(``mg_per_kg_per_day`` 80, ``max_mg_per_day`` 3000, ``doses_per_day`` 2).
The engine applies that rule; it does not choose it.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from ent.engines.prescriptions.errors import EngineInputError
from ent.engines.prescriptions.pediatric_dosing import (
    VERSION,
    AgeCap,
    DosingRule,
    PediatricDoseInput,
    weight_based_dose,
)
from ent.engines.registry import registered_calculators

_RULE = DosingRule(
    mg_per_kg_per_day=Decimal("80"),
    doses_per_day=2,
    max_mg_per_day=Decimal("3000"),
)


def _flag(result_flags: tuple[object, ...], code: str) -> dict[str, str]:
    for flag in result_flags:
        if getattr(flag, "code", None) == code:
            detail = getattr(flag, "detail", {})
            return dict(detail)
    msg = f"missing flag {code}"
    raise AssertionError(msg)


@pytest.mark.clinical
def test_architecture_rule_at_ten_kilograms() -> None:
    """10 kg * 80 mg/kg/day = 800 mg/day = 400 mg/dose; 25 mg/mL -> 16 mL."""

    result = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("10"),
            rule=_RULE,
            concentration_mg_per_ml=Decimal("25"),
            completed_years=4,
        )
    )
    assert result.version == VERSION
    assert result.unit == "mg"
    assert result.value == "400.000"
    assert _flag(result.flags, "mg_per_day")["value"] == "800.000"
    assert _flag(result.flags, "mg_per_kg_per_day_rule")["value"] == "80"
    assert _flag(result.flags, "doses_per_day")["value"] == "2"
    assert _flag(result.flags, "volume_ml") == {"value": "16.00", "unit": "mL"}
    assert result.inputs["weight_kg"] == "10"
    assert all(flag.code != "dose_above_maximum" for flag in result.flags)


@pytest.mark.clinical
def test_daily_dose_equal_to_the_maximum_is_not_above_it() -> None:
    """37.5 kg * 80 = 3000 mg/day, which is the supplied maximum."""

    result = weight_based_dose(
        PediatricDoseInput(weight_kg=Decimal("37.5"), rule=_RULE)
    )
    assert _flag(result.flags, "mg_per_day")["value"] == "3000.000"
    assert result.value == "1500.000"
    assert all(flag.code != "dose_above_maximum" for flag in result.flags)
    assert _flag(result.flags, "volume_unavailable") == {}


@pytest.mark.clinical
def test_daily_dose_above_the_supplied_maximum_is_flagged_and_not_replaced() -> None:
    """38 kg * 80 = 3040 mg/day. The calculated dose stays 3040."""

    result = weight_based_dose(PediatricDoseInput(weight_kg=Decimal("38"), rule=_RULE))
    assert _flag(result.flags, "mg_per_day")["value"] == "3040.000"
    assert result.value == "1520.000"
    above = _flag(result.flags, "dose_above_maximum")
    assert above["daily_mg"] == "3040.000"
    assert above["max_mg_per_day"] == "3000.000"


@pytest.mark.clinical
def test_age_cap_is_an_input_and_the_narrowest_covering_band_wins() -> None:
    """Age 1 uses the 2-year cap of 500 mg; age 5 uses the 12-year cap."""

    caps = (
        AgeCap(max_completed_years=12, max_mg_per_day=Decimal("1000")),
        AgeCap(max_completed_years=2, max_mg_per_day=Decimal("500")),
    )
    infant = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("10"),
            rule=_RULE,
            completed_years=1,
            age_caps=caps,
        )
    )
    assert _flag(infant.flags, "dose_above_maximum")["max_mg_per_day"] == "500.000"

    child = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("13"),
            rule=_RULE,
            completed_years=5,
            age_caps=caps,
        )
    )
    assert _flag(child.flags, "dose_above_maximum")["max_mg_per_day"] == "1000.000"

    older = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("10"),
            rule=_RULE,
            completed_years=13,
            age_caps=caps,
        )
    )
    assert all(flag.code != "dose_above_maximum" for flag in older.flags)


@pytest.mark.clinical
def test_uneven_split_quantizes_half_up_to_milligrams() -> None:
    """100 mg/day over 3 doses is 33.333 mg per dose (half up at 0.001)."""

    result = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("1"),
            rule=DosingRule(
                mg_per_kg_per_day=Decimal("100"),
                doses_per_day=3,
                max_mg_per_day=Decimal("5000"),
            ),
        )
    )
    assert result.value == "33.333"
    assert _flag(result.flags, "mg_per_day")["value"] == "100.000"


@pytest.mark.clinical
def test_daily_dose_scales_with_weight_when_under_the_maximum() -> None:
    """Doubling a weight that stays under the maximum doubles the daily dose."""

    light = weight_based_dose(PediatricDoseInput(weight_kg=Decimal("5"), rule=_RULE))
    heavy = weight_based_dose(PediatricDoseInput(weight_kg=Decimal("10"), rule=_RULE))
    assert Decimal(_flag(heavy.flags, "mg_per_day")["value"]) == (
        Decimal(_flag(light.flags, "mg_per_day")["value"]) * 2
    )


@pytest.mark.clinical
@pytest.mark.parametrize(
    ("weight", "code"),
    [
        (Decimal("0"), "prescription.dosing_weight_invalid"),
        (Decimal("-1"), "prescription.dosing_weight_invalid"),
    ],
)
def test_non_positive_weight_is_rejected(weight: Decimal, code: str) -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(PediatricDoseInput(weight_kg=weight, rule=_RULE))
    assert caught.value.code == code


@pytest.mark.clinical
def test_missing_age_when_caps_exist_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=_RULE,
                age_caps=(
                    AgeCap(max_completed_years=2, max_mg_per_day=Decimal("500")),
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_age_required"


@pytest.mark.clinical
def test_zero_mg_per_kg_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=DosingRule(
                    mg_per_kg_per_day=Decimal("0"),
                    max_mg_per_day=None,
                    doses_per_day=2,
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_rule_invalid"


@pytest.mark.clinical
def test_doses_per_day_below_one_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=DosingRule(
                    mg_per_kg_per_day=Decimal("80"),
                    max_mg_per_day=None,
                    doses_per_day=0,
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_frequency_invalid"


@pytest.mark.clinical
def test_negative_age_cap_years_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=_RULE,
                completed_years=1,
                age_caps=(
                    AgeCap(max_completed_years=-1, max_mg_per_day=Decimal("100")),
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_age_invalid"


@pytest.mark.clinical
def test_negative_completed_years_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=_RULE,
                completed_years=-1,
                age_caps=(
                    AgeCap(max_completed_years=2, max_mg_per_day=Decimal("500")),
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_age_invalid"


@pytest.mark.clinical
def test_invalid_maximum_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=DosingRule(
                    mg_per_kg_per_day=Decimal("80"),
                    max_mg_per_day=Decimal("0"),
                    doses_per_day=2,
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_max_invalid"


@pytest.mark.clinical
def test_age_cap_is_the_maximum_when_the_rule_has_none() -> None:
    result = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("10"),
            rule=DosingRule(
                mg_per_kg_per_day=Decimal("80"),
                doses_per_day=2,
                indication_code="otitis",
            ),
            completed_years=1,
            age_caps=(AgeCap(max_completed_years=2, max_mg_per_day=Decimal("500")),),
        )
    )
    assert _flag(result.flags, "mg_per_day")["value"] == "800.000"
    assert _flag(result.flags, "dose_above_maximum")["max_mg_per_day"] == "500.000"
    assert result.inputs["indication_code"] == "otitis"


@pytest.mark.clinical
def test_a_rule_without_a_maximum_does_not_flag_the_dose() -> None:
    result = weight_based_dose(
        PediatricDoseInput(
            weight_kg=Decimal("10"),
            rule=DosingRule(mg_per_kg_per_day=Decimal("80"), doses_per_day=2),
        )
    )
    assert result.value == "400.000"
    assert all(flag.code != "dose_above_maximum" for flag in result.flags)


@pytest.mark.clinical
def test_an_invalid_age_cap_maximum_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=DosingRule(mg_per_kg_per_day=Decimal("80"), doses_per_day=2),
                completed_years=1,
                age_caps=(AgeCap(max_completed_years=2, max_mg_per_day=Decimal("0")),),
            )
        )
    assert caught.value.code == "prescription.dosing_max_invalid"


@pytest.mark.clinical
def test_non_finite_milligrams_per_kilogram_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=DosingRule(
                    mg_per_kg_per_day=Decimal("NaN"),
                    doses_per_day=2,
                ),
            )
        )
    assert caught.value.code == "prescription.dosing_rule_invalid"


@pytest.mark.clinical
def test_non_finite_weight_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(PediatricDoseInput(weight_kg=Decimal("NaN"), rule=_RULE))
    assert caught.value.code == "prescription.dosing_weight_invalid"


def test_zero_concentration_is_rejected() -> None:
    with pytest.raises(EngineInputError) as caught:
        weight_based_dose(
            PediatricDoseInput(
                weight_kg=Decimal("10"),
                rule=_RULE,
                concentration_mg_per_ml=Decimal("0"),
            )
        )
    assert caught.value.code == "prescription.dosing_concentration_invalid"


@pytest.mark.clinical
def test_calculator_is_registered() -> None:
    codes = {spec.code for spec in registered_calculators()}
    assert "prescriptions.pediatric_dose" in codes
    assert "prescriptions.steroid_taper" in codes
