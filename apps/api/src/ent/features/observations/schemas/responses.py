"""Observation read models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class ObservationComponentRead(CamelModel):
    public_id: str
    concept: CodeableConcept
    value_type: str
    value_concept: CodeableConcept | None = None
    value_numeric: Decimal | None = None
    value_unit: str | None = None
    value_boolean: bool | None = None
    value_text: str | None = None
    value_low: Decimal | None = None
    value_high: Decimal | None = None
    ordinal_value: int | None = None
    qualifiers: dict[str, Any] | None = None


class ObservationRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    concept: CodeableConcept
    body_site: CodeableConcept | None = None
    map_region_code: str | None = None
    laterality: str
    status: str
    value_type: str
    value_concept: CodeableConcept | None = None
    value_numeric: Decimal | None = None
    value_unit: str | None = None
    value_boolean: bool | None = None
    value_text: str | None = None
    value_low: Decimal | None = None
    value_high: Decimal | None = None
    ordinal_value: int | None = None
    qualifiers: dict[str, Any] | None = None
    effective_at: datetime
    source: str
    recorded_by_public_id: str | None = None
    confirmed_by_public_id: str | None = None
    method: CodeableConcept | None = None
    components: list[ObservationComponentRead]
    version: int


class ObservationDiffSide(CamelModel):
    public_id: str | None = None
    status: str | None = None
    ordinal_value: int | None = None
    value_numeric: Decimal | None = None
    value_text: str | None = None
    value_concept: CodeableConcept | None = None


class ObservationDiffRead(CamelModel):
    body_site: CodeableConcept | None = None
    map_region_code: str | None = None
    laterality: str
    concept: CodeableConcept
    visit_a: ObservationDiffSide
    visit_b: ObservationDiffSide


class ExaminationSnapshotRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    map_id: str
    laterality: str | None
    payload: dict[str, Any]
    rendered_svg_public_id: str | None = None
    version: int
