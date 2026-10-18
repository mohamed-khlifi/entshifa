"""Threshold validation on audiogram request schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ent.features.audiology.schemas.requests import ThresholdInput


def test_threshold_requires_level_when_not_no_response() -> None:
    with pytest.raises(ValidationError):
        ThresholdInput(
            ear="right",
            conduction="air",
            frequency_hz=1000,
            level_db=None,
            is_no_response=False,
        )


def test_bone_conduction_rejects_extended_high_frequency() -> None:
    with pytest.raises(ValidationError):
        ThresholdInput(
            ear="left",
            conduction="bone",
            frequency_hz=10000,
            level_db=30,
        )


def test_no_response_allows_limit_level() -> None:
    row = ThresholdInput(
        ear="right",
        conduction="air",
        frequency_hz=4000,
        level_db=120,
        is_no_response=True,
    )
    assert row.level_db == 120
    assert row.is_no_response is True
