"""Canonical SHA-256 of a procedure at the moment it is signed (architecture §30)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

VERSION = "1.0.0"
REFERENCE = (
    "Architecture §30 and feature spec §7: signing stores a SHA-256 of the "
    "canonical procedure content with the signer, timestamp and IP. Addenda "
    "are the only legal change after that hash. Child exams (endoscopy, "
    "laryngoscopy, otology) extend this parent; they do not replace it."
)


@dataclass(frozen=True, slots=True)
class ProcedureContent:
    """The procedure fields that must not change after signing."""

    procedure_public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    procedure_concept_code: str
    performed_at: str
    performed_by_public_id: str
    laterality: str
    anesthesia: str
    setting: str
    instrument: str | None
    indication_text: str | None
    tolerance: str | None
    complication_concept_code: str | None
    complication_note: str | None


def canonical_json(content: ProcedureContent) -> str:
    """Stable JSON: sorted keys, UTF-8, no insignificant whitespace."""

    payload = {
        "anesthesia": content.anesthesia,
        "complicationConceptCode": content.complication_concept_code,
        "complicationNote": content.complication_note,
        "encounterPublicId": content.encounter_public_id,
        "indicationText": content.indication_text,
        "instrument": content.instrument,
        "laterality": content.laterality,
        "patientPublicId": content.patient_public_id,
        "performedAt": content.performed_at,
        "performedByPublicId": content.performed_by_public_id,
        "procedureConceptCode": content.procedure_concept_code,
        "procedurePublicId": content.procedure_public_id,
        "setting": content.setting,
        "tolerance": content.tolerance,
    }
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def locked_hash(content: ProcedureContent) -> str:
    """SHA-256 hex digest of :func:`canonical_json`."""

    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def hashes_match(content: ProcedureContent, digest: str) -> bool:
    """True when ``digest`` is the hash of this content."""

    return locked_hash(content) == digest
