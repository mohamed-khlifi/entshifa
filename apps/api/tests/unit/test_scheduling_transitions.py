"""Unit tests for appointment status transitions."""

from __future__ import annotations

import pytest

from ent.features.scheduling.transitions import can_transition


@pytest.mark.parametrize(
    ("from_status", "to_status", "expected"),
    [
        ("scheduled", "arrived", True),
        ("scheduled", "cancelled", True),
        ("scheduled", "completed", False),
        ("arrived", "in_room", True),
        ("in_room", "completed", True),
        ("completed", "arrived", False),
        ("cancelled", "arrived", False),
    ],
)
def test_can_transition(from_status: str, to_status: str, expected: bool) -> None:
    assert can_transition(from_status, to_status) is expected
