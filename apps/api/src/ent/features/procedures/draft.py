"""Apply a draft procedure update. Signed rows never reach this module."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ent.core.errors.exceptions import ValidationError
from ent.core.security.principal import CurrentUser
from ent.features.procedures.constants import COMPLICATION_KINDS
from ent.features.procedures.exceptions import ProcedureConceptInvalidError
from ent.features.procedures.mapping import blank_to_none, to_utc_naive
from ent.features.procedures.models import ProcedureRecord
from ent.features.procedures.references import ProcedureReferences
from ent.features.terminology.models import Concept

_REQUIRED = frozenset(
    {
        "laterality",
        "anesthesia",
        "setting",
        "performed_at",
        "procedure_concept_public_id",
        "performed_by_public_id",
    }
)


def reject_null_required(data: dict[str, Any]) -> None:
    missing = sorted(key for key in _REQUIRED if key in data and data[key] is None)
    if missing:
        raise ValidationError(reason="required", field=missing[0])


async def load_procedure_concepts(
    refs: ProcedureReferences,
    user: CurrentUser,
    procedure_public_id: str,
    complication_public_id: str | None,
) -> dict[str, Concept]:
    public_ids = {procedure_public_id}
    if complication_public_id is not None:
        public_ids.add(complication_public_id)
    concepts = await refs.concepts(user, public_ids)
    require_procedure_kind(
        concepts[procedure_public_id], role="procedure", expected="procedure"
    )
    if complication_public_id is not None:
        _optional_id(concepts, complication_public_id)
    return concepts


async def apply_draft_changes(
    refs: ProcedureReferences,
    user: CurrentUser,
    row: ProcedureRecord,
    data: dict[str, Any],
) -> None:
    procedure_public_id = data.get("procedure_concept_public_id")
    complication_present = "complication_concept_public_id" in data
    complication_public_id = data.get("complication_concept_public_id")
    wanted = {
        public_id
        for public_id in (procedure_public_id, complication_public_id)
        if isinstance(public_id, str)
    }
    concepts = await refs.concepts(user, wanted) if wanted else {}
    if isinstance(procedure_public_id, str):
        require_procedure_kind(
            concepts[procedure_public_id], role="procedure", expected="procedure"
        )
        row.procedure_concept_id = int(concepts[procedure_public_id].id)
    if complication_present:
        row.complication_concept_id = _optional_id(concepts, complication_public_id)
    if "encounter_public_id" in data:
        row.encounter_id = await refs.encounter_id(
            user,
            _optional_str(data["encounter_public_id"]),
            patient_id=int(row.patient_id),
        )
    if "performed_at" in data and isinstance(data["performed_at"], datetime):
        row.performed_at = to_utc_naive(data["performed_at"])
    if isinstance(data.get("performed_by_public_id"), str):
        row.performed_by_id = await refs.member_id(
            user, str(data["performed_by_public_id"])
        )
    if "laterality" in data:
        row.laterality = _text(data["laterality"])
    if "anesthesia" in data:
        row.anesthesia = str(data["anesthesia"])
    if "setting" in data:
        row.setting = str(data["setting"])
    if "instrument" in data:
        row.instrument = blank_to_none(_optional_str(data["instrument"]))
    if "indication_text" in data:
        row.indication_text = blank_to_none(_optional_str(data["indication_text"]))
    if "tolerance" in data:
        tolerance = data["tolerance"]
        row.tolerance = None if tolerance is None else str(tolerance)
    if "complication_note" in data:
        row.complication_note = blank_to_none(_optional_str(data["complication_note"]))


def require_procedure_kind(concept: Concept, *, role: str, expected: str) -> None:
    if concept.kind != expected:
        raise ProcedureConceptInvalidError(
            concept_public_id=concept.public_id,
            kind=concept.kind,
            role=role,
        )


def _optional_id(concepts: dict[str, Concept], public_id: str | None) -> int | None:
    if public_id is None:
        return None
    concept = concepts[public_id]
    if concept.kind not in COMPLICATION_KINDS:
        raise ProcedureConceptInvalidError(
            concept_public_id=concept.public_id,
            kind=concept.kind,
            role="complication",
        )
    return int(concept.id)


def _text(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
