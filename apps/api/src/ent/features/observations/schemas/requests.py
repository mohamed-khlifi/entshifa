"""Observation write payloads."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality

ValueType = Literal["code", "numeric", "boolean", "text", "range", "ordinal"]
ObservationStatus = Literal["normal", "abnormal", "not_examined", "unknown"]
ObservationSource = Literal[
    "clinician",
    "technician",
    "patient",
    "device",
    "ai_confirmed",
]


class ObservationValueFields(CamelModel):
    value_type: ValueType
    value_concept_code: str | None = Field(default=None, max_length=60)
    value_numeric: Decimal | None = None
    value_unit: str | None = Field(default=None, max_length=20)
    value_boolean: bool | None = None
    value_text: str | None = Field(default=None, max_length=500)
    value_low: Decimal | None = None
    value_high: Decimal | None = None
    ordinal_value: int | None = Field(default=None, ge=-32768, le=32767)
    qualifiers: dict[str, Any] | None = None


class ObservationComponentCreate(ObservationValueFields):
    concept_code: str = Field(min_length=1, max_length=60)


class ObservationCreate(ObservationValueFields):
    concept_code: str = Field(min_length=1, max_length=60)
    body_site_code: str | None = Field(default=None, max_length=60)
    map_region_code: str | None = Field(default=None, max_length=80)
    laterality: Laterality
    status: ObservationStatus
    effective_at: datetime
    source: ObservationSource = "clinician"
    confirmed: bool = False
    method_concept_code: str | None = Field(default=None, max_length=60)
    components: list[ObservationComponentCreate] = Field(default_factory=list)


class ObservationBatchCreate(CamelModel):
    encounter_public_id: str = Field(min_length=26, max_length=26)
    observations: list[ObservationCreate] = Field(min_length=1, max_length=100)


class ObservationUpdate(ObservationValueFields):
    version: int = Field(ge=1)
    status: ObservationStatus
    map_region_code: str | None = Field(default=None, max_length=80)


class ExaminationSnapshotCreate(CamelModel):
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    map_id: str = Field(min_length=1, max_length=60)
    laterality: Laterality | None = None
    payload: dict[str, Any]
    rendered_svg_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
