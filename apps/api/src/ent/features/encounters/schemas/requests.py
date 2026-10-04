"""Encounter write payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality
from ent.features.diagnoses.schemas.requests import DiagnosisWrite

EncounterType = Literal[
    "consultation",
    "follow_up",
    "procedure",
    "post_op",
    "result_review",
    "teleconsultation",
]

_TEXT = 65_000


class EncounterComplaintWrite(CamelModel):
    concept_code: str = Field(min_length=1, max_length=60)
    is_primary: bool = False
    laterality: Laterality | None = None
    duration_text: str | None = Field(default=None, max_length=60)
    sort_order: int = Field(default=0, ge=0, le=1000)


class EncounterCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    site_public_id: str = Field(min_length=26, max_length=26)
    appointment_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    template_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    encounter_type: EncounterType = "consultation"
    started_at: datetime
    ended_at: datetime | None = None
    chief_complaint_summary: str | None = Field(default=None, max_length=255)
    history_text: str | None = Field(default=None, max_length=_TEXT)
    assessment_text: str | None = Field(default=None, max_length=_TEXT)
    plan_text: str | None = Field(default=None, max_length=_TEXT)
    complaints: list[EncounterComplaintWrite] = Field(
        default_factory=list, max_length=20
    )
    diagnoses: list[DiagnosisWrite] = Field(default_factory=list, max_length=30)


class EncounterPatch(CamelModel):
    version: int = Field(ge=1)
    ended_at: datetime | None = None
    chief_complaint_summary: str | None = Field(default=None, max_length=255)
    history_text: str | None = Field(default=None, max_length=_TEXT)
    assessment_text: str | None = Field(default=None, max_length=_TEXT)
    plan_text: str | None = Field(default=None, max_length=_TEXT)
    complaints: list[EncounterComplaintWrite] | None = Field(
        default=None, max_length=20
    )
    diagnoses: list[DiagnosisWrite] | None = Field(default=None, max_length=30)


class EncounterSign(CamelModel):
    role: str = Field(
        default="clinician",
        min_length=1,
        max_length=30,
        pattern=r"^[a-z][a-z0-9_]*$",
    )


class EncounterAddendumCreate(CamelModel):
    body: str = Field(min_length=1, max_length=_TEXT)


class EncounterCopyForward(CamelModel):
    started_at: datetime
    site_public_id: str | None = Field(default=None, min_length=26, max_length=26)


class HistoryFieldConfig(CamelModel):
    id: str = Field(min_length=1, max_length=60)
    label_key: str = Field(min_length=1, max_length=120)
    field_type: Literal["text", "boolean", "select", "multiselect", "number"]
    options: list[str] | None = None
    required: bool = False
    default_value: Any | None = None


class EncounterTemplateConfig(CamelModel):
    history_fields: list[HistoryFieldConfig] = Field(default_factory=list)
    exam_sections: list[str] = Field(default_factory=list)
    suggested_instruments: list[str] = Field(default_factory=list)
    suggested_tests: list[str] = Field(default_factory=list)
    suggested_documents: list[str] = Field(default_factory=list)
    favorite_diagnoses: list[str] = Field(default_factory=list)
    default_follow_up_days: int | None = Field(default=None, ge=1, le=730)


class EncounterTemplateOverrideWrite(CamelModel):
    name_key: str | None = Field(default=None, max_length=80)
    trigger_concept_codes: list[str] | None = None
    config: EncounterTemplateConfig


class EncounterTemplateRouteRequest(CamelModel):
    complaint_codes: list[str] = Field(default_factory=list, max_length=20)
    primary_complaint_code: str | None = Field(default=None, max_length=60)
