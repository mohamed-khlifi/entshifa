"""Map encounter rows to wire models. No HTTP and no queries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import CodeableConcept
from ent.engines.encounters.signing import (
    ComplaintSnapshot,
    DiagnosisSnapshot,
    EncounterContent,
)
from ent.features.diagnoses.mapping import to_diagnosis_read
from ent.features.encounters.models import (
    Encounter,
    EncounterAddendum,
    EncounterComplaint,
    EncounterSignature,
    EncounterTemplate,
)
from ent.features.encounters.schemas.requests import EncounterComplaintWrite
from ent.features.encounters.schemas.responses import (
    EncounterAddendumRead,
    EncounterComplaintRead,
    EncounterRead,
    EncounterSignatureRead,
    EncounterTemplateRead,
)

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


def normalize_complaints(
    items: list[EncounterComplaintWrite],
) -> list[EncounterComplaintWrite]:
    """One primary complaint. The earliest sort order becomes primary if none is."""

    if sum(1 for item in items if item.is_primary) > 1:
        raise ValidationError(reason="multiple_primary")
    if items and not any(item.is_primary for item in items):
        index = min(range(len(items)), key=lambda i: (items[i].sort_order, i))
        items[index] = items[index].model_copy(update={"is_primary": True})
    return items


def assert_time_range(started_at: datetime, ended_at: datetime | None) -> None:
    if ended_at is not None and ended_at < started_at:
        raise ValidationError(reason="ended_at")


def content_from_encounter(encounter: Encounter) -> EncounterContent:
    active = [row for row in encounter.complaints if row.deleted_at is None]
    previous = encounter.previous_encounter
    return EncounterContent(
        encounter_public_id=encounter.public_id,
        patient_public_id=encounter.patient.public_id,
        encounter_type=encounter.encounter_type,
        started_at=instant_token(encounter.started_at) or "",
        ended_at=instant_token(encounter.ended_at),
        chief_complaint_summary=encounter.chief_complaint_summary,
        history_text=encounter.history_text,
        assessment_text=encounter.assessment_text,
        plan_text=encounter.plan_text,
        previous_encounter_public_id=(
            previous.public_id if previous is not None else None
        ),
        complaints=tuple(
            ComplaintSnapshot(
                concept_code=row.concept.code,
                is_primary=bool(row.is_primary),
                laterality=row.laterality,
                duration_text=row.duration_text,
                sort_order=int(row.sort_order),
            )
            for row in active
        ),
        diagnoses=tuple(
            DiagnosisSnapshot(
                concept_code=row.concept.code,
                laterality=row.laterality,
                status=row.status,
                is_primary=bool(row.is_primary),
                sort_order=int(row.sort_order),
            )
            for row in encounter.diagnoses
            if row.deleted_at is None
        ),
    )


def to_encounter_read(encounter: Encounter, labels: _LABELS) -> EncounterRead:
    complaints = [
        _complaint(row, labels)
        for row in encounter.complaints
        if row.deleted_at is None
    ]
    addenda = [_addendum(row) for row in encounter.addenda if row.deleted_at is None]
    signatures = [
        _signature(row) for row in encounter.signatures if row.deleted_at is None
    ]
    appointment = encounter.appointment
    template = encounter.template
    previous = encounter.previous_encounter
    signed_by = encounter.signed_by
    return EncounterRead(
        public_id=encounter.public_id,
        patient_public_id=encounter.patient.public_id,
        site_public_id=encounter.site.public_id,
        clinician_public_id=encounter.clinician.public_id,
        appointment_public_id=(
            appointment.public_id if appointment is not None else None
        ),
        template_public_id=template.public_id if template is not None else None,
        encounter_type=encounter.encounter_type,
        started_at=encounter.started_at,
        ended_at=encounter.ended_at,
        chief_complaint_summary=encounter.chief_complaint_summary,
        history_text=encounter.history_text,
        assessment_text=encounter.assessment_text,
        plan_text=encounter.plan_text,
        status=encounter.status,
        signed_at=encounter.signed_at,
        signed_by_public_id=signed_by.public_id if signed_by is not None else None,
        locked_hash=encounter.locked_hash,
        previous_encounter_public_id=(
            previous.public_id if previous is not None else None
        ),
        complaints=complaints,
        diagnoses=[
            to_diagnosis_read(row, labels)
            for row in encounter.diagnoses
            if row.deleted_at is None
        ],
        addenda=addenda,
        signatures=signatures,
        version=int(encounter.version),
    )


def to_page(
    items: list[EncounterRead],
    *,
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[EncounterRead]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset or 0, next_cursor=None),
    )


def _complaint(row: EncounterComplaint, labels: _LABELS) -> EncounterComplaintRead:
    labeled = labels.get(int(row.concept_id))
    if labeled is None:
        concept = CodeableConcept(
            concept_id=row.concept.public_id,
            code=row.concept.code,
            display=None,
        )
    else:
        public_id, code, display = labeled
        concept = CodeableConcept(concept_id=public_id, code=code, display=display)
    return EncounterComplaintRead(
        public_id=row.public_id,
        concept=concept,
        is_primary=bool(row.is_primary),
        laterality=row.laterality,
        duration_text=row.duration_text,
        sort_order=int(row.sort_order),
    )


def _addendum(row: EncounterAddendum) -> EncounterAddendumRead:
    return EncounterAddendumRead(
        public_id=row.public_id,
        author_public_id=row.author.public_id,
        body=row.body,
        created_at=row.created_at,
    )


def _signature(row: EncounterSignature) -> EncounterSignatureRead:
    return EncounterSignatureRead(
        public_id=row.public_id,
        user_public_id=row.signer.public_id,
        role=row.role,
        signed_at=row.signed_at,
        content_hash=row.content_hash,
    )


def template_to_read(
    row: EncounterTemplate,
    trigger_concepts: list[CodeableConcept],
) -> EncounterTemplateRead:
    scope: Literal["system", "clinic", "doctor"]
    if row.user_id is not None:
        scope = "doctor"
    elif row.clinic_id is not None:
        scope = "clinic"
    else:
        scope = "system"

    return EncounterTemplateRead(
        public_id=row.public_id,
        code=row.code,
        name_key=row.name_key,
        scope=scope,
        is_active=bool(row.is_active),
        trigger_concepts=trigger_concepts,
        config=row.config or {},
        version=int(row.version),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
