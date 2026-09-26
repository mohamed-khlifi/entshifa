"""Unit tests for storage key layout."""

from __future__ import annotations

import pytest

from ent.integrations.storage.keys import build_storage_key, variant_storage_key


def test_build_storage_key_with_patient() -> None:
    key = build_storage_key(
        clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB0",
        category="clinical_photo",
        object_ulid="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        extension="jpg",
    )
    assert key == (
        "clinic/01ARZ3NDEKTSV4RRFFQ69G5FAV/patient/01ARZ3NDEKTSV4RRFFQ69G5FB0/"
        "clinical_photo/01ARZ3NDEKTSV4RRFFQ69G5FB1.jpg"
    )


def test_build_storage_key_clinic_scoped() -> None:
    key = build_storage_key(
        clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        patient_public_id=None,
        category="logo",
        object_ulid="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        extension="png",
    )
    assert "/patient/_none/logo/" in key


def test_variant_storage_key() -> None:
    original = (
        "clinic/01ARZ3NDEKTSV4RRFFQ69G5FAV/patient/_none/"
        "clinical_photo/01ARZ3NDEKTSV4RRFFQ69G5FB1.jpg"
    )
    assert variant_storage_key(original, variant="thumb").endswith("__thumb.jpg")


def test_rejects_bad_category() -> None:
    with pytest.raises(ValueError):
        build_storage_key(
            clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            patient_public_id=None,
            category="../evil",
            object_ulid="01ARZ3NDEKTSV4RRFFQ69G5FB1",
            extension="jpg",
        )
