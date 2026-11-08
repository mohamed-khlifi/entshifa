"""P5-05 calculator input parsers — clinical coverage."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from ent.engines.audiology.types import ABG_FREQUENCIES_HZ, AIR_CONFIG_FREQUENCIES_HZ
from ent.engines.calculator_errors import CalculatorInputError
from ent.engines.calculator_parsers import (
    collect_thresholds,
    domain_from_code,
    optional_bool,
    optional_date,
    optional_decimal,
    optional_int,
    optional_str,
    require_bool,
    require_date,
    require_decimal,
    require_int,
    require_str,
    threshold_level,
)


@pytest.mark.clinical
def test_require_and_optional_scalars() -> None:
    raw = {
        "name": "ok",
        "n": "4",
        "flag": "yes",
        "amount": "12.5",
        "d": "2024-06-01",
    }
    assert require_str(raw, "name") == "ok"
    assert optional_str(raw, "missing") is None
    assert require_int(raw, "n", minimum=0, maximum=10) == 4
    assert optional_int(raw, "missing", minimum=0, maximum=10) is None
    assert require_bool(raw, "flag") is True
    assert require_bool({"flag": False}, "flag") is False
    assert optional_bool(raw, "missing") is None
    assert require_decimal(raw, "amount") == Decimal("12.5")
    assert optional_decimal(raw, "missing") is None
    assert require_date(raw, "d") == date(2024, 6, 1)
    assert optional_date(raw, "missing") is None


@pytest.mark.clinical
@pytest.mark.parametrize(
    "key,fn",
    [
        ("name", lambda r: require_str(r, "name")),
        ("n", lambda r: require_int(r, "n", minimum=None, maximum=None)),
        ("flag", lambda r: require_bool(r, "flag")),
        ("amount", lambda r: require_decimal(r, "amount")),
        ("d", lambda r: require_date(r, "d")),
    ],
)
def test_missing_required_fields(key: str, fn) -> None:
    with pytest.raises(CalculatorInputError) as exc:
        fn({})
    assert exc.value.code == "calculator.missing_field"


@pytest.mark.clinical
def test_invalid_integer_boolean_and_date() -> None:
    with pytest.raises(CalculatorInputError):
        require_int({"n": "x"}, "n", minimum=None, maximum=None)
    with pytest.raises(CalculatorInputError):
        require_int({"n": True}, "n", minimum=None, maximum=None)
    with pytest.raises(CalculatorInputError):
        require_int({"n": "5"}, "n", minimum=0, maximum=3)
    assert require_bool({"flag": "no"}, "flag") is False
    with pytest.raises(CalculatorInputError):
        require_bool({"flag": "maybe"}, "flag")
    with pytest.raises(CalculatorInputError):
        require_date({"d": "not-a-date"}, "d")
    assert optional_bool({"flag": "1"}, "flag") is True
    assert optional_bool({"flag": ""}, "flag") is None
    with pytest.raises(CalculatorInputError):
        require_decimal({"amount": "not"}, "amount")
    with pytest.raises(CalculatorInputError):
        optional_date({"d": "2024-13-40"}, "d")


@pytest.mark.clinical
def test_int_range_and_threshold_collection() -> None:
    with pytest.raises(CalculatorInputError):
        require_int({"n": "99"}, "n", minimum=0, maximum=10)
    with pytest.raises(CalculatorInputError) as exc:
        require_int({"n": "-1"}, "n", minimum=0, maximum=120)
    assert exc.value.code == "calculator.out_of_range"
    raw = {f"air_right_{f}": "25" for f in (500, 1000, 2000)}
    assert threshold_level(raw, conduction="air", ear="right", frequency_hz=500) == 25
    points = collect_thresholds(raw, frequencies_hz=(500, 1000, 2000))
    assert len(points) == 3
    with pytest.raises(CalculatorInputError):
        threshold_level(
            {}, conduction="air", ear="right", frequency_hz=500, required=True
        )


@pytest.mark.clinical
def test_domain_from_code() -> None:
    assert domain_from_code("audiology.pta") == "audiology"


@pytest.mark.clinical
def test_bilateral_threshold_matrix() -> None:
    raw: dict[str, str] = {}
    for ear in ("right", "left"):
        for conduction in ("air", "bone"):
            freqs = (
                ABG_FREQUENCIES_HZ
                if conduction == "bone"
                else AIR_CONFIG_FREQUENCIES_HZ
            )
            for hz in freqs:
                raw[f"{conduction}_{ear}_{hz}"] = "30"
    points = collect_thresholds(
        raw,
        frequencies_hz=AIR_CONFIG_FREQUENCIES_HZ,
        conductions=("air", "bone"),
    )
    assert len(points) > 0
