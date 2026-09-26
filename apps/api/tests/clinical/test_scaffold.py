"""Scaffold for known-answer cases; calculators add rows under tests/clinical/."""

from __future__ import annotations

import pytest


@pytest.mark.clinical
def test_clinical_suite_is_wired() -> None:
    """Ensures the clinical marker is collected in CI until engines ship."""
    assert True
