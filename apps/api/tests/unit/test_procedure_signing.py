"""Known-answer checks for the procedure signing hash (architecture §30)."""

from __future__ import annotations

import hashlib
from typing import get_args

from ent.engines.procedures.signing import (
    REFERENCE,
    VERSION,
    ProcedureContent,
    canonical_json,
    hashes_match,
    locked_hash,
)
from ent.features.procedures.constants import (
    ANESTHESIA_TYPES,
    PROCEDURE_SETTINGS,
    PROCEDURE_STATUSES,
    TOLERANCE_VALUES,
    AnesthesiaType,
    ProcedureSetting,
    ProcedureStatus,
    ToleranceValue,
)

_CANONICAL = (
    '{"anesthesia":"topical_spray","complicationConceptCode":null,'
    '"complicationNote":null,"encounterPublicId":"01ARZ3NDEKTSV4RRFFQ69G5FAX",'
    '"indicationText":"epistaxis","instrument":"rigid 0","laterality":"right",'
    '"patientPublicId":"01ARZ3NDEKTSV4RRFFQ69G5FAW",'
    '"performedAt":"2026-06-02T09:00:00.000000",'
    '"performedByPublicId":"01ARZ3NDEKTSV4RRFFQ69G5FAY",'
    '"procedureConceptCode":"PROC.NASAL_ENDOSCOPY",'
    '"procedurePublicId":"01ARZ3NDEKTSV4RRFFQ69G5FAV","setting":"office",'
    '"tolerance":"well_tolerated"}'
)


def _content(*, laterality: str = "right") -> ProcedureContent:
    return ProcedureContent(
        procedure_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
        encounter_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAX",
        procedure_concept_code="PROC.NASAL_ENDOSCOPY",
        performed_at="2026-06-02T09:00:00.000000",
        performed_by_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAY",
        laterality=laterality,
        anesthesia="topical_spray",
        setting="office",
        instrument="rigid 0",
        indication_text="epistaxis",
        tolerance="well_tolerated",
        complication_concept_code=None,
        complication_note=None,
    )


def test_signing_version_is_recorded() -> None:
    assert VERSION == "1.0.0"
    assert "Architecture §30" in REFERENCE


def test_locked_hash_matches_canonical_json() -> None:
    content = _content()
    assert canonical_json(content) == _CANONICAL
    digest = hashlib.sha256(_CANONICAL.encode("utf-8")).hexdigest()
    assert locked_hash(content) == digest
    assert hashes_match(content, digest)
    assert not hashes_match(content, "0" * 64)


def test_laterality_changes_the_locked_hash() -> None:
    assert locked_hash(_content()) != locked_hash(_content(laterality="left"))


def test_allowed_values_match_the_schema_literals() -> None:
    assert set(get_args(ProcedureStatus)) == set(PROCEDURE_STATUSES)
    assert set(get_args(ProcedureSetting)) == set(PROCEDURE_SETTINGS)
    assert set(get_args(AnesthesiaType)) == set(ANESTHESIA_TYPES)
    assert set(get_args(ToleranceValue)) == set(TOLERANCE_VALUES)
