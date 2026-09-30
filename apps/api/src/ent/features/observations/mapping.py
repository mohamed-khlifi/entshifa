"""Map observation drafts and rows. No HTTP and no queries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import CodeableConcept
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.observations.types import (
    ComponentDraft,
    ObservationDraft,
    ValueDraft,
)
from ent.engines.observations.validation import (
    ObservationValueError,
    validate_observation_value,
)
from ent.features.observations.exceptions import ObservationInvalidValueError
from ent.features.observations.models import (
    ExaminationSnapshot,
    Observation,
    ObservationComponent,
)
from ent.features.observations.repository import ObservationDiffRow
from ent.features.observations.schemas.requests import (
    ObservationCreate,
    ObservationValueFields,
)
from ent.features.observations.schemas.responses import (
    ExaminationSnapshotRead,
    ObservationComponentRead,
    ObservationDiffRead,
    ObservationDiffSide,
    ObservationRead,
)
from ent.features.patients.models import Patient
from ent.features.terminology.models import Concept

_LABELS = dict[int, tuple[str, str, str | None]]


def _check(value: ValueDraft) -> None:
    try:
        validate_observation_value(value)
    except ObservationValueError as exc:
        raise ObservationInvalidValueError(reason=exc.reason) from exc


def _draft(body: ObservationCreate) -> ObservationDraft:
    return ObservationDraft(
        concept_code=body.concept_code,
        body_site_code=body.body_site_code,
        map_region_code=body.map_region_code,
        laterality=body.laterality.value,
        status=body.status,
        value=_value_draft(body),
        components=tuple(
            ComponentDraft(concept_code=item.concept_code, value=_value_draft(item))
            for item in body.components
        ),
        effective_at=_to_utc_naive(body.effective_at),
        source=body.source,
        confirmed=body.confirmed,
        method_concept_code=body.method_concept_code,
    )


def _value_draft(body: ObservationValueFields) -> ValueDraft:
    text = body.value_text.strip() if body.value_text else None
    return ValueDraft(
        value_type=body.value_type,
        value_concept_code=body.value_concept_code,
        value_numeric=body.value_numeric,
        value_unit=body.value_unit,
        value_boolean=body.value_boolean,
        value_text=text or None,
        value_low=body.value_low,
        value_high=body.value_high,
        ordinal_value=body.ordinal_value,
        qualifiers=body.qualifiers,
    )


def _codes(drafts: tuple[ObservationDraft, ...]) -> set[str]:
    codes: set[str] = set()
    for draft in drafts:
        codes.add(draft.concept_code)
        if draft.body_site_code:
            codes.add(draft.body_site_code)
        if draft.method_concept_code:
            codes.add(draft.method_concept_code)
        codes.update(_value_codes(draft.value))
        for component in draft.components:
            codes.add(component.concept_code)
            codes.update(_value_codes(component.value))
    return codes


def _value_codes(value: ValueDraft) -> set[str]:
    if value.value_concept_code:
        return {value.value_concept_code}
    return set()


def _observation(
    *,
    user: CurrentUser,
    patient: Patient,
    encounter_public_id: str,
    draft: ObservationDraft,
    concepts: dict[str, Concept],
) -> Observation:
    return Observation(
        public_id=new_ulid(),
        clinic_id=user.clinic_id,
        patient_id=int(patient.id),
        encounter_public_id=encounter_public_id,
        concept_id=int(concepts[draft.concept_code].id),
        body_site_concept_id=_concept_id(concepts, draft.body_site_code),
        map_region_code=draft.map_region_code,
        laterality=draft.laterality,
        status=draft.status,
        effective_at=draft.effective_at,
        source=draft.source,
        recorded_by_id=user.user_id,
        confirmed_by_id=user.user_id if draft.confirmed else None,
        method_concept_id=_concept_id(concepts, draft.method_concept_code),
        created_by_id=user.user_id,
        updated_by_id=user.user_id,
        **_value_columns(draft.value, concepts),
    )


def _component(
    user: CurrentUser,
    observation: Observation,
    draft: ComponentDraft,
    concepts: dict[str, Concept],
) -> ObservationComponent:
    return ObservationComponent(
        public_id=new_ulid(),
        clinic_id=user.clinic_id,
        observation_id=int(observation.id) if observation.id is not None else 0,
        concept_id=int(concepts[draft.concept_code].id),
        created_by_id=user.user_id,
        updated_by_id=user.user_id,
        **_value_columns(draft.value, concepts),
    )


def _apply_value(
    row: Observation,
    value: ValueDraft,
    concepts: dict[str, Concept],
) -> None:
    applied = _value_columns(value, concepts)
    row.value_type = str(applied["value_type"])
    row.value_concept_id = applied["value_concept_id"]
    row.value_numeric = applied["value_numeric"]
    row.value_unit = applied["value_unit"]
    row.value_boolean = applied["value_boolean"]
    row.value_text = applied["value_text"]
    row.value_low = applied["value_low"]
    row.value_high = applied["value_high"]
    row.ordinal_value = applied["ordinal_value"]
    row.qualifiers = applied["qualifiers"]


def _value_columns(
    value: ValueDraft,
    concepts: dict[str, Concept],
) -> dict[str, Any]:
    concept_id = _concept_id(concepts, value.value_concept_code)
    if value.value_type == "code" and concept_id is None:
        raise ObservationInvalidValueError(reason="concept")
    return {
        "value_type": value.value_type,
        "value_concept_id": concept_id,
        "value_numeric": value.value_numeric,
        "value_unit": value.value_unit,
        "value_boolean": value.value_boolean,
        "value_text": value.value_text,
        "value_low": value.value_low,
        "value_high": value.value_high,
        "ordinal_value": value.ordinal_value,
        "qualifiers": dict(value.qualifiers) if value.qualifiers is not None else None,
    }


def _concept_id(concepts: dict[str, Concept], code: str | None) -> int | None:
    if code is None:
        return None
    return int(concepts[code].id)


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _concept_ids(rows: list[Observation]) -> set[int]:
    found: set[int] = set()
    for row in rows:
        found.add(int(row.concept_id))
        for field in ("body_site_concept_id", "value_concept_id", "method_concept_id"):
            value = getattr(row, field)
            if value is not None:
                found.add(int(value))
        for component in row.components:
            found.add(int(component.concept_id))
            if component.value_concept_id is not None:
                found.add(int(component.value_concept_id))
    return found


def _user_ids(rows: list[Observation]) -> set[int]:
    found: set[int] = set()
    for row in rows:
        if row.recorded_by_id is not None:
            found.add(int(row.recorded_by_id))
        if row.confirmed_by_id is not None:
            found.add(int(row.confirmed_by_id))
    return found


def _page(
    items: list[Any],
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[Any]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset or 0, next_cursor=None),
    )


def _labeled(labels: _LABELS, concept_id: int | None) -> CodeableConcept | None:
    if concept_id is None:
        return None
    public_id, code, display = labels[concept_id]
    return CodeableConcept(concept_id=public_id, code=code, display=display)


def _observation_read(
    row: Observation,
    patient_public_id: str,
    labels: _LABELS,
    users: dict[int, str],
) -> ObservationRead:
    recorded = users.get(int(row.recorded_by_id)) if row.recorded_by_id else None
    confirmed = users.get(int(row.confirmed_by_id)) if row.confirmed_by_id else None
    return ObservationRead(
        public_id=row.public_id,
        patient_public_id=patient_public_id,
        encounter_public_id=row.encounter_public_id,
        concept=_labeled(labels, int(row.concept_id)) or CodeableConcept(concept_id=""),
        body_site=_labeled(labels, _optional_int(row.body_site_concept_id)),
        map_region_code=row.map_region_code,
        laterality=str(row.laterality),
        status=row.status,
        value_type=row.value_type,
        value_concept=_labeled(labels, _optional_int(row.value_concept_id)),
        value_numeric=row.value_numeric,
        value_unit=row.value_unit,
        value_boolean=row.value_boolean,
        value_text=row.value_text,
        value_low=row.value_low,
        value_high=row.value_high,
        ordinal_value=row.ordinal_value,
        qualifiers=row.qualifiers if isinstance(row.qualifiers, dict) else None,
        effective_at=row.effective_at,
        source=row.source,
        recorded_by_public_id=recorded,
        confirmed_by_public_id=confirmed,
        method=_labeled(labels, _optional_int(row.method_concept_id)),
        components=[_component_read(component, labels) for component in row.components],
        version=int(row.version),
    )


def _component_read(
    row: ObservationComponent,
    labels: _LABELS,
) -> ObservationComponentRead:
    concept = _labeled(labels, int(row.concept_id))
    return ObservationComponentRead(
        public_id=row.public_id,
        concept=concept or CodeableConcept(concept_id=""),
        value_type=row.value_type,
        value_concept=_labeled(labels, _optional_int(row.value_concept_id)),
        value_numeric=row.value_numeric,
        value_unit=row.value_unit,
        value_boolean=row.value_boolean,
        value_text=row.value_text,
        value_low=row.value_low,
        value_high=row.value_high,
        ordinal_value=row.ordinal_value,
        qualifiers=row.qualifiers if isinstance(row.qualifiers, dict) else None,
    )


def _diff_read(row: ObservationDiffRow, labels: _LABELS) -> ObservationDiffRead:
    concept = _labeled(labels, row.concept_id)
    return ObservationDiffRead(
        body_site=_labeled(labels, row.body_site_concept_id),
        map_region_code=row.map_region_code,
        laterality=row.laterality,
        concept=concept or CodeableConcept(concept_id=""),
        visit_a=ObservationDiffSide(
            public_id=row.public_id_a,
            status=row.status_a,
            ordinal_value=row.ordinal_a,
            value_numeric=row.numeric_a,
            value_text=row.text_a,
            value_concept=_labeled(labels, row.value_concept_id_a),
        ),
        visit_b=ObservationDiffSide(
            public_id=row.public_id_b,
            status=row.status_b,
            ordinal_value=row.ordinal_b,
            value_numeric=row.numeric_b,
            value_text=row.text_b,
            value_concept=_labeled(labels, row.value_concept_id_b),
        ),
    )


def _snapshot_read(
    row: ExaminationSnapshot,
    patient_public_id: str,
    rendered_svg_public_id: str | None,
) -> ExaminationSnapshotRead:
    payload = row.payload if isinstance(row.payload, dict) else {}
    laterality = row.laterality if isinstance(row.laterality, str) else None
    return ExaminationSnapshotRead(
        public_id=row.public_id,
        patient_public_id=patient_public_id,
        encounter_public_id=row.encounter_public_id,
        map_id=row.map_id,
        laterality=laterality,
        payload=payload,
        rendered_svg_public_id=rendered_svg_public_id,
        version=int(row.version),
    )


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | str):
        msg = "expected an integer"
        raise TypeError(msg)
    return int(value)
