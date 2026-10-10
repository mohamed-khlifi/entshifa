"""Known-answer cases for the day-by-day decrement generator.

The worked example is the generator's own specification (P2-08):
start 60 mg, step 10 mg, 2 days at each dose, floor 10 mg.
It is not a published steroid protocol.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from ent.engines.prescriptions.errors import EngineInputError
from ent.engines.prescriptions.steroid_taper import (
    VERSION,
    TaperInput,
    generate_steroid_taper,
)


@pytest.mark.clinical
def test_sixty_milligram_step_holds_each_dose_for_two_days() -> None:
    """60, 60, 50, 50, ... 10, 10. Fourteen days. The next dose would be 0."""

    result = generate_steroid_taper(
        TaperInput(
            start_mg=Decimal("60"),
            step_mg=Decimal("10"),
            days_per_step=2,
            minimum_mg=Decimal("10"),
        )
    )
    doses = [day.dose_mg for day in result.days]
    assert doses == [
        Decimal("60.000"),
        Decimal("60.000"),
        Decimal("50.000"),
        Decimal("50.000"),
        Decimal("40.000"),
        Decimal("40.000"),
        Decimal("30.000"),
        Decimal("30.000"),
        Decimal("20.000"),
        Decimal("20.000"),
        Decimal("10.000"),
        Decimal("10.000"),
    ]
    assert result.calculation.version == VERSION
    assert result.calculation.value == "12"
    assert result.calculation.unit == "day"
    assert result.calculation.flags[0].detail["days"].startswith("60.000,60.000,50.000")


@pytest.mark.clinical
def test_a_step_that_skips_the_floor_stops_before_it() -> None:
    """25 then 15. The following 5 mg is below the 10 mg floor and is omitted."""

    result = generate_steroid_taper(
        TaperInput(
            start_mg=Decimal("25"),
            step_mg=Decimal("10"),
            days_per_step=1,
            minimum_mg=Decimal("10"),
        )
    )
    assert [day.dose_mg for day in result.days] == [
        Decimal("25.000"),
        Decimal("15.000"),
    ]
    assert [day.day_number for day in result.days] == [1, 2]


@pytest.mark.clinical
def test_zero_floor_stops_before_a_non_positive_dose() -> None:
    result = generate_steroid_taper(
        TaperInput(
            start_mg=Decimal("30"),
            step_mg=Decimal("10"),
            days_per_step=1,
            minimum_mg=Decimal("0"),
        )
    )
    assert [day.dose_mg for day in result.days] == [
        Decimal("30.000"),
        Decimal("20.000"),
        Decimal("10.000"),
    ]


@pytest.mark.clinical
@pytest.mark.parametrize(
    "payload",
    [
        TaperInput(
            start_mg=Decimal("0"),
            step_mg=Decimal("10"),
            days_per_step=1,
            minimum_mg=Decimal("0"),
        ),
        TaperInput(
            start_mg=Decimal("10"),
            step_mg=Decimal("0"),
            days_per_step=1,
            minimum_mg=Decimal("0"),
        ),
        TaperInput(
            start_mg=Decimal("10"),
            step_mg=Decimal("5"),
            days_per_step=0,
            minimum_mg=Decimal("0"),
        ),
        TaperInput(
            start_mg=Decimal("5"),
            step_mg=Decimal("1"),
            days_per_step=1,
            minimum_mg=Decimal("10"),
        ),
        TaperInput(
            start_mg=Decimal("10"),
            step_mg=Decimal("1"),
            days_per_step=1,
            minimum_mg=Decimal("-1"),
        ),
    ],
)
def test_invalid_taper_inputs_are_rejected(payload: TaperInput) -> None:
    with pytest.raises(EngineInputError) as caught:
        generate_steroid_taper(payload)
    assert caught.value.code == "prescription.taper_input_invalid"


@pytest.mark.clinical
@pytest.mark.parametrize(
    "payload",
    [
        TaperInput(
            start_mg=Decimal("NaN"),
            step_mg=Decimal("10"),
            days_per_step=2,
            minimum_mg=Decimal("10"),
        ),
        TaperInput(
            start_mg=Decimal("60"),
            step_mg=Decimal("NaN"),
            days_per_step=2,
            minimum_mg=Decimal("10"),
        ),
        TaperInput(
            start_mg=Decimal("60"),
            step_mg=Decimal("10"),
            days_per_step=2,
            minimum_mg=Decimal("NaN"),
        ),
    ],
)
def test_non_finite_taper_values_are_rejected(payload: TaperInput) -> None:
    with pytest.raises(EngineInputError) as caught:
        generate_steroid_taper(payload)
    assert caught.value.code == "prescription.taper_input_invalid"


@pytest.mark.clinical
def test_a_runaway_step_is_rejected() -> None:
    """A 0.001 mg step from 1 mg would exceed the 366-day guard."""

    with pytest.raises(EngineInputError) as caught:
        generate_steroid_taper(
            TaperInput(
                start_mg=Decimal("1"),
                step_mg=Decimal("0.001"),
                days_per_step=400,
                minimum_mg=Decimal("0"),
            )
        )
    assert caught.value.code == "prescription.taper_too_long"
