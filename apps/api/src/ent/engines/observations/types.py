"""Value shapes for observation rows (architecture §25.6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Mapping

VALUE_TYPES = ("code", "numeric", "boolean", "text", "range", "ordinal")
OBSERVATION_STATUSES = ("normal", "abnormal", "not_examined", "unknown")
OBSERVATION_SOURCES = (
    "clinician",
    "technician",
    "patient",
    "device",
    "ai_confirmed",
)
LATERALITIES = ("right", "left", "bilateral", "midline", "na")


@dataclass(frozen=True, slots=True)
class ValueDraft:
    """One typed value. Exactly one value family is populated."""

    value_type: str
    value_concept_code: str | None = None
    value_numeric: Decimal | None = None
    value_unit: str | None = None
    value_boolean: bool | None = None
    value_text: str | None = None
    value_low: Decimal | None = None
    value_high: Decimal | None = None
    ordinal_value: int | None = None
    qualifiers: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ComponentDraft:
    """A part of a multi-part finding (size, quadrant, edge)."""

    concept_code: str
    value: ValueDraft


@dataclass(frozen=True, slots=True)
class ObservationDraft:
    """A finding before it is split by side or written."""

    concept_code: str
    body_site_code: str | None
    map_region_code: str | None
    laterality: str
    status: str
    value: ValueDraft
    components: tuple[ComponentDraft, ...]
    effective_at: datetime
    source: str
    confirmed: bool
    method_concept_code: str | None
