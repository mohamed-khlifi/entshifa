"""Map diagnosis rows to wire models. No HTTP and no queries."""

from __future__ import annotations

from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.common import CodeableConcept
from ent.features.diagnoses.models import Diagnosis, UserDiagnosisFavorite
from ent.features.diagnoses.schemas.requests import DiagnosisWrite
from ent.features.diagnoses.schemas.responses import (
    DiagnosisFavoriteRead,
    DiagnosisRead,
)

_LABELS = dict[int, tuple[str, str, str | None]]


def normalize_diagnoses(items: list[DiagnosisWrite]) -> list[DiagnosisWrite]:
    """One primary diagnosis. The earliest sort order becomes primary if none is."""

    if sum(1 for item in items if item.is_primary) > 1:
        raise ValidationError(reason="multiple_primary")
    if items and not any(item.is_primary for item in items):
        index = min(range(len(items)), key=lambda i: (items[i].sort_order, i))
        items[index] = items[index].model_copy(update={"is_primary": True})
    return items


def problem_status_for(diagnosis_status: str) -> str:
    """Problem-list status used when a visit diagnosis is promoted."""

    if diagnosis_status == "confirmed":
        return "active"
    return diagnosis_status


def to_diagnosis_read(row: Diagnosis, labels: _LABELS) -> DiagnosisRead:
    promoted = row.promoted_problem
    derived = row.derived_from
    promoted_id = None
    if promoted is not None and promoted.deleted_at is None:
        promoted_id = promoted.public_id
    derived_id = None
    if derived is not None and derived.deleted_at is None:
        derived_id = derived.public_id
    return DiagnosisRead(
        public_id=row.public_id,
        concept=_concept(row.concept_id, row.concept, labels),
        laterality=row.laterality,
        status=row.status,
        is_primary=bool(row.is_primary),
        onset_date=row.onset_date,
        note=row.note,
        sort_order=int(row.sort_order),
        source=row.source,
        promoted_problem_public_id=promoted_id,
        derived_from_public_id=derived_id,
    )


def to_favorite_read(
    row: UserDiagnosisFavorite, labels: _LABELS
) -> DiagnosisFavoriteRead:
    return DiagnosisFavoriteRead(
        concept=_concept(row.concept_id, row.concept, labels),
        sort_order=int(row.sort_order),
    )


def _concept(
    concept_id: int,
    concept: object,
    labels: _LABELS,
) -> CodeableConcept:
    labeled = labels.get(int(concept_id))
    if labeled is None:
        public_id = str(getattr(concept, "public_id", ""))
        code = getattr(concept, "code", None)
        return CodeableConcept(
            concept_id=public_id,
            code=str(code) if code is not None else None,
            display=None,
        )
    public_id, code, display = labeled
    return CodeableConcept(concept_id=public_id, code=code, display=display)
