"""Encounter read models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept
from ent.features.diagnoses.schemas.responses import DiagnosisRead


class EncounterComplaintRead(CamelModel):
    public_id: str
    concept: CodeableConcept
    is_primary: bool
    laterality: str | None = None
    duration_text: str | None = None
    sort_order: int


class EncounterAddendumRead(CamelModel):
    public_id: str
    author_public_id: str
    body: str
    created_at: datetime


class EncounterSignatureRead(CamelModel):
    public_id: str
    user_public_id: str
    role: str
    signed_at: datetime
    content_hash: str


class EncounterRead(CamelModel):
    public_id: str
    patient_public_id: str
    site_public_id: str
    clinician_public_id: str
    appointment_public_id: str | None = None
    template_public_id: str | None = None
    encounter_type: str
    started_at: datetime
    ended_at: datetime | None = None
    chief_complaint_summary: str | None = None
    history_text: str | None = None
    assessment_text: str | None = None
    plan_text: str | None = None
    status: str
    signed_at: datetime | None = None
    signed_by_public_id: str | None = None
    locked_hash: str | None = None
    previous_encounter_public_id: str | None = None
    complaints: list[EncounterComplaintRead]
    diagnoses: list[DiagnosisRead] = Field(default_factory=list)
    addenda: list[EncounterAddendumRead]
    signatures: list[EncounterSignatureRead]
    version: int


class EncounterTemplateRead(CamelModel):
    public_id: str
    code: str
    name_key: str
    scope: Literal["system", "clinic", "doctor"]
    is_active: bool
    trigger_concepts: list[CodeableConcept] = Field(default_factory=list)
    config: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime
