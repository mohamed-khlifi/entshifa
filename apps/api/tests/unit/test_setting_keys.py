"""Unit tests for clinical setting key validation."""

from __future__ import annotations

import pytest

from ent.core.errors.exceptions import ValidationError
from ent.features.clinics.setting_keys import validate_setting_value


def test_validate_pta_formula() -> None:
    assert validate_setting_value("pta_formula", "4freq_who") == "4freq_who"


def test_validate_pta_formula_rejects_unknown() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_setting_value("pta_formula", "iso7029")
    assert exc.value.context["reason"] == "invalid_pta_formula"


def test_validate_asymmetry_rule() -> None:
    value = validate_setting_value(
        "asymmetry_rule",
        {
            "adjacent_db": 15,
            "adjacent_count": 2,
            "single_db": 20,
            "wrs_percent": 15,
        },
    )
    assert value["adjacent_db"] == 15


def test_validate_unknown_key() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_setting_value("not_a_real_key", "x")
    assert exc.value.context["reason"] == "unknown_setting_key"


def test_validate_polyp_scale_accepts_lildholdt() -> None:
    assert validate_setting_value("polyp_scale", "lildholdt") == "lildholdt"
    assert validate_setting_value("polyp_scale", "meltzer") == "meltzer"


def test_validate_shift_rule() -> None:
    value = validate_setting_value("shift_rule", {"rule": "asha"})
    assert value["rule"] == "asha"


def test_validate_polyp_scale_rejects_item_scale_name() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_setting_value("polyp_scale", "lund_kennedy")
    assert exc.value.context["reason"] == "invalid_polyp_scale"
