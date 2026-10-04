"""Canonical SHA-256 of a visit at the moment it is signed (architecture §30)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

VERSION = "1.1.0"
REFERENCE = (
    "Architecture §30: signing stores a SHA-256 of the canonical visit content "
    "with the signer, timestamp and IP so a later check can prove the record "
    "was not altered. Addenda are the only legal change after that hash. "
    "Version 1.1.0 includes coded diagnoses (concept, side, status, primary, order)."
)


@dataclass(frozen=True, slots=True)
class ComplaintSnapshot:
    """One coded complaint included in the signed content."""

    concept_code: str
    is_primary: bool
    laterality: str | None
    duration_text: str | None
    sort_order: int


@dataclass(frozen=True, slots=True)
class DiagnosisSnapshot:
    """One coded diagnosis included in the signed content."""

    concept_code: str
    laterality: str
    status: str
    is_primary: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class EncounterContent:
    """The visit fields that must not change after signing."""

    encounter_public_id: str
    patient_public_id: str
    encounter_type: str
    started_at: str
    ended_at: str | None
    chief_complaint_summary: str | None
    history_text: str | None
    assessment_text: str | None
    plan_text: str | None
    previous_encounter_public_id: str | None
    complaints: tuple[ComplaintSnapshot, ...]
    diagnoses: tuple[DiagnosisSnapshot, ...] = ()


def canonical_json(content: EncounterContent) -> str:
    """Stable JSON: sorted keys, UTF-8, complaints ordered by sort then code."""

    complaints = sorted(
        content.complaints,
        key=lambda item: (item.sort_order, item.concept_code, item.laterality or ""),
    )
    diagnoses = sorted(
        content.diagnoses,
        key=lambda item: (item.sort_order, item.concept_code, item.laterality),
    )
    payload = {
        "assessmentText": content.assessment_text,
        "chiefComplaintSummary": content.chief_complaint_summary,
        "complaints": [
            {
                "conceptCode": item.concept_code,
                "durationText": item.duration_text,
                "isPrimary": item.is_primary,
                "laterality": item.laterality,
                "sortOrder": item.sort_order,
            }
            for item in complaints
        ],
        "diagnoses": [
            {
                "conceptCode": item.concept_code,
                "isPrimary": item.is_primary,
                "laterality": item.laterality,
                "sortOrder": item.sort_order,
                "status": item.status,
            }
            for item in diagnoses
        ],
        "encounterPublicId": content.encounter_public_id,
        "encounterType": content.encounter_type,
        "endedAt": content.ended_at,
        "historyText": content.history_text,
        "patientPublicId": content.patient_public_id,
        "planText": content.plan_text,
        "previousEncounterPublicId": content.previous_encounter_public_id,
        "startedAt": content.started_at,
    }
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def locked_hash(content: EncounterContent) -> str:
    """SHA-256 hex digest of :func:`canonical_json`."""

    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def hashes_match(content: EncounterContent, digest: str) -> bool:
    """True when ``digest`` is the hash of this content."""

    return locked_hash(content) == digest
