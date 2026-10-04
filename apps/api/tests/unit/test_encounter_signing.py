"""Known-answer checks for the encounter signing hash (architecture §30)."""

from __future__ import annotations

import hashlib

from ent.engines.encounters.signing import (
    VERSION,
    ComplaintSnapshot,
    EncounterContent,
    canonical_json,
    hashes_match,
    locked_hash,
)

_CANONICAL = (
    '{"assessmentText":null,"chiefComplaintSummary":"otalgia",'
    '"complaints":['
    '{"conceptCode":"CC.EAR_PAIN","durationText":"3 days","isPrimary":true,'
    '"laterality":"right","sortOrder":0},'
    '{"conceptCode":"CC.TINNITUS","durationText":null,"isPrimary":false,'
    '"laterality":"left","sortOrder":1}'
    '],"diagnoses":[],"encounterPublicId":"01ARZ3NDEKTSV4RRFFQ69G5FAV",'
    '"encounterType":"consultation","endedAt":null,"historyText":"sudden",'
    '"patientPublicId":"01ARZ3NDEKTSV4RRFFQ69G5FAW","planText":null,'
    '"previousEncounterPublicId":null,"startedAt":"2026-06-01T09:00:00.000000"}'
)


def _content(*, reversed_complaints: bool = False) -> EncounterContent:
    ear = ComplaintSnapshot(
        concept_code="CC.EAR_PAIN",
        is_primary=True,
        laterality="right",
        duration_text="3 days",
        sort_order=0,
    )
    tinnitus = ComplaintSnapshot(
        concept_code="CC.TINNITUS",
        is_primary=False,
        laterality="left",
        duration_text=None,
        sort_order=1,
    )
    complaints = (tinnitus, ear) if reversed_complaints else (ear, tinnitus)
    return EncounterContent(
        encounter_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
        encounter_type="consultation",
        started_at="2026-06-01T09:00:00.000000",
        ended_at=None,
        chief_complaint_summary="otalgia",
        history_text="sudden",
        assessment_text=None,
        plan_text=None,
        previous_encounter_public_id=None,
        complaints=complaints,
    )


def test_signing_version_is_recorded() -> None:
    assert VERSION == "1.1.0"


def test_locked_hash_matches_canonical_json() -> None:
    content = _content()
    assert canonical_json(content) == _CANONICAL
    digest = hashlib.sha256(_CANONICAL.encode("utf-8")).hexdigest()
    assert locked_hash(content) == digest
    assert hashes_match(content, digest)
    assert not hashes_match(content, "0" * 64)


def test_complaint_order_does_not_change_the_hash() -> None:
    assert locked_hash(_content()) == locked_hash(_content(reversed_complaints=True))


def test_diagnosis_changes_the_locked_hash() -> None:
    from ent.engines.encounters.signing import DiagnosisSnapshot

    plain = _content()
    coded = EncounterContent(
        encounter_public_id=plain.encounter_public_id,
        patient_public_id=plain.patient_public_id,
        encounter_type=plain.encounter_type,
        started_at=plain.started_at,
        ended_at=plain.ended_at,
        chief_complaint_summary=plain.chief_complaint_summary,
        history_text=plain.history_text,
        assessment_text=plain.assessment_text,
        plan_text=plain.plan_text,
        previous_encounter_public_id=plain.previous_encounter_public_id,
        complaints=plain.complaints,
        diagnoses=(
            DiagnosisSnapshot(
                concept_code="H60.9",
                laterality="right",
                status="confirmed",
                is_primary=True,
                sort_order=0,
            ),
        ),
    )
    assert locked_hash(plain) != locked_hash(coded)
    rendered = canonical_json(coded)
    assert '"conceptCode":"H60.9"' in rendered
    assert '"status":"confirmed"' in rendered


def test_unicode_history_is_not_escaped() -> None:
    content = EncounterContent(
        encounter_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        patient_public_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
        encounter_type="consultation",
        started_at="2026-06-01T09:00:00.000000",
        ended_at=None,
        chief_complaint_summary=None,
        history_text="Bén",
        assessment_text=None,
        plan_text=None,
        previous_encounter_public_id=None,
        complaints=(
            ComplaintSnapshot(
                concept_code="CC.EAR_PAIN",
                is_primary=True,
                laterality=None,
                duration_text=None,
                sort_order=0,
            ),
        ),
    )
    rendered = canonical_json(content)
    assert "Bén" in rendered
    assert "\\u" not in rendered
    assert '"laterality":null' in rendered
