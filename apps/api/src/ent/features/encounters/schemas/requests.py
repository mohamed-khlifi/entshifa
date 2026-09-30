"""Encounter write payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality

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
