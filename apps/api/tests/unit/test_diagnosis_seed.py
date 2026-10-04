"""ICD-10 ENT seed covers every complaint-template favourite."""

from __future__ import annotations

from ent.seeds.encounter_templates import SYSTEM_TEMPLATES
from ent.seeds.icd10_ent import ICD10_CODES, ICD10_ENT, LOCAL_DIAGNOSES


def test_icd_codes_are_unique() -> None:
    codes = [code for code, _en, _fr in ICD10_ENT]
    assert len(codes) == len(set(codes))
    assert len(ICD10_ENT) >= 100


def test_template_favorite_diagnoses_are_seeded() -> None:
    missing: list[str] = []
    for template in SYSTEM_TEMPLATES:
        favorites = template.config.get("favoriteDiagnoses", [])
        assert isinstance(favorites, list)
        for code in favorites:
            if code not in ICD10_CODES:
                missing.append(f"{template.code}:{code}")
    assert missing == []


def test_local_codes_map_to_seeded_icd() -> None:
    for code, _en, _fr, target in LOCAL_DIAGNOSES:
        assert code.startswith("LOCAL.")
        assert target in ICD10_CODES
