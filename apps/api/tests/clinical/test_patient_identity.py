"""Known-answer tests for patient name folding and duplicate detection.

Reference: Unicode Standard Annex #15 (NFKD) and feature specification §4.1.
"""

from __future__ import annotations

from datetime import date

import pytest

from ent.engines.patients.duplicates import VERSION as DUPLICATE_VERSION
from ent.engines.patients.duplicates import is_likely_duplicate
from ent.engines.patients.name_normalize import VERSION as NAME_VERSION
from ent.engines.patients.name_normalize import (
    build_name_normalized,
    fold_name_part,
    normalize_phone,
)


@pytest.mark.clinical
def test_accented_latin_name_folds_to_the_unaccented_form() -> None:
    """Bén Alï and Ben Ali share one search key (UAX #15 NFKD + case fold)."""

    assert NAME_VERSION == "1.0.0"
    assert fold_name_part("Bén") == "ben"
    assert fold_name_part("Alï") == "ali"
    folded = build_name_normalized(first_name="Bén", last_name="Alï")
    assert folded == "ben ali"
    assert fold_name_part("Ben Ali") in folded


@pytest.mark.clinical
def test_duplicate_folded_name_tokens_are_deduped_once() -> None:
    """Same token in first and last name must not appear twice in the search key."""

    folded = build_name_normalized(first_name="Ben", last_name="ben")
    assert folded == "ben"


@pytest.mark.clinical
def test_arabic_script_is_preserved_beside_the_latin_name() -> None:
    """The second script stays in the search key; it is not transliterated."""

    folded = build_name_normalized(
        first_name="Bén",
        last_name="Alï",
        first_name_alt="بن",
        last_name_alt="علي",
    )
    assert "ben" in folded
    assert "ali" in folded
    assert "بن" in folded
    assert "علي" in folded
    assert fold_name_part("بن علي") in folded


@pytest.mark.clinical
def test_phone_formatting_does_not_hide_the_same_number() -> None:
    assert normalize_phone("+216 12 345 678") == "21612345678"
    assert normalize_phone("21612345678") == "21612345678"
    assert normalize_phone("   ") is None


@pytest.mark.clinical
def test_duplicate_rule_matches_name_and_birth_date_or_phone() -> None:
    """Feature spec §4.1: same name plus birth date, or the same phone."""

    assert DUPLICATE_VERSION == "1.0.0"
    birth = date(1980, 4, 2)
    assert is_likely_duplicate(
        left_name_normalized="ben ali",
        left_birth_date=birth,
        left_phones=(None, None),
        right_name_normalized="ben ali",
        right_birth_date=birth,
        right_phones=(None, None),
    )
    assert not is_likely_duplicate(
        left_name_normalized="ben ali",
        left_birth_date=birth,
        left_phones=(None, None),
        right_name_normalized="ben ali",
        right_birth_date=date(1981, 4, 2),
        right_phones=(None, None),
    )
    assert is_likely_duplicate(
        left_name_normalized="other",
        left_birth_date=birth,
        left_phones=("21611111111", None),
        right_name_normalized="different",
        right_birth_date=date(1990, 1, 1),
        right_phones=(None, "21611111111"),
    )
