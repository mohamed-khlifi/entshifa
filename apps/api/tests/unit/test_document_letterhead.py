"""Letterhead placeholder checks and preview sample data."""

from __future__ import annotations

import pytest

from ent.core.errors.exceptions import ValidationError
from ent.features.documents.letterhead import (
    sample_placeholder_data,
    validate_letterhead_html,
)


def test_sample_data_nests_lists_and_scalars() -> None:
    data = sample_placeholder_data(
        {
            "patient.fullName": {"type": "string"},
            "patient.ageYears": {"type": "integer"},
            "patient.allergies": {"type": "text_list"},
        }
    )
    assert data["patient"]["fullName"] == ""
    assert data["patient"]["ageYears"] == 0
    assert data["patient"]["allergies"] == []


def test_letterhead_rejects_an_undeclared_placeholder() -> None:
    with pytest.raises(ValidationError):
        validate_letterhead_html("<p>{{ patient.secret }}</p>")


def test_letterhead_accepts_clinic_fields() -> None:
    validate_letterhead_html("<p>{{ clinic.name }}</p>")
