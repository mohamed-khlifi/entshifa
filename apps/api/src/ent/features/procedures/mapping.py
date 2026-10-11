"""Map procedure rows to read models and to the signing snapshot."""

from __future__ import annotations

from datetime import UTC, datetime

from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import CodeableConcept
from ent.engines.procedures.signing import ProcedureContent
from ent.features.procedures.models import ProcedureRecord, ProcedureRecordAddendum
from ent.features.procedures.schemas.responses import (
    ProcedureAddendumRead,
    ProcedureRecordRead,
)
from ent.features.users.models import User

_LABELS = dict[int, tuple[str, str, str | None]]


def to_utc_naive(value: datetime) -> datetime:
    """Persist an aware instant as naive UTC DATETIME(6)."""

    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def instant_token(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f")


def blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def display_name(user: User) -> str:
    return f"{user.first_name} {user.last_name}".strip()


def content_from_record(row: ProcedureRecord) -> ProcedureContent:
    """Clinical content covered by the locked hash. Addenda are excluded."""

    encounter = row.encounter
    complication = row.complication_concept
    return ProcedureContent(
        procedure_public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=encounter.public_id if encounter is not None else None,
        procedure_concept_code=row.procedure_concept.code,
        performed_at=instant_token(row.performed_at) or "",
        performed_by_public_id=row.performed_by.public_id,
        laterality=row.laterality,
        anesthesia=row.anesthesia,
        setting=row.setting,
        instrument=row.instrument,
        indication_text=row.indication_text,
        tolerance=row.tolerance,
        complication_concept_code=(
            complication.code if complication is not None else None
        ),
        complication_note=row.complication_note,
    )


def to_procedure_read(row: ProcedureRecord, labels: _LABELS) -> ProcedureRecordRead:
    encounter = row.encounter
    signed_by = row.signed_by
    addenda = [_addendum(item) for item in row.addenda if item.deleted_at is None]
    return ProcedureRecordRead(
        public_id=row.public_id,
        patient_id=row.patient.public_id,
        patient_display_name=display_name_patient(row),
        encounter_id=encounter.public_id if encounter is not None else None,
        procedure=_concept(
            int(row.procedure_concept_id), row.procedure_concept, labels
        ),
        performed_at=row.performed_at,
        performed_by_id=row.performed_by.public_id,
        performed_by_display_name=display_name(row.performed_by),
        laterality=row.laterality,
        anesthesia=row.anesthesia,
        setting=row.setting,
        instrument=row.instrument,
        indication_text=row.indication_text,
        tolerance=row.tolerance,
        complication=(
            _concept(int(row.complication_concept_id), row.complication_concept, labels)
            if row.complication_concept_id is not None
            and row.complication_concept is not None
            else None
        ),
        complication_note=row.complication_note,
        status=row.status,
        signed_at=row.signed_at,
        signed_by_id=signed_by.public_id if signed_by is not None else None,
        signed_role=row.signed_role,
        locked_hash=row.locked_hash,
        version=int(row.version),
        created_at=row.created_at,
        updated_at=row.updated_at,
        addenda=addenda,
    )


def to_page(
    items: list[ProcedureRecordRead],
    *,
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[ProcedureRecordRead]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset, next_cursor=None),
    )


def display_name_patient(row: ProcedureRecord) -> str:
    patient = row.patient
    return f"{patient.first_name} {patient.last_name}".strip()


def _addendum(row: ProcedureRecordAddendum) -> ProcedureAddendumRead:
    return ProcedureAddendumRead(
        public_id=row.public_id,
        author_public_id=row.author.public_id,
        author_display_name=display_name(row.author),
        body=row.body,
        created_at=row.created_at,
    )


def _concept(
    concept_id: int,
    concept: object,
    labels: _LABELS,
) -> CodeableConcept:
    labeled = labels.get(concept_id)
    if labeled is None:
        public_id = str(getattr(concept, "public_id", ""))
        code = getattr(concept, "code", None)
        return CodeableConcept(
            concept_id=public_id,
            code=str(code) if code is not None else None,
        )
    public_id, code, display = labeled
    return CodeableConcept(concept_id=public_id, code=code, display=display)
