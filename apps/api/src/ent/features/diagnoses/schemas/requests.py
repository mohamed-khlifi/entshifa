"""Diagnosis write payloads."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality

DiagnosisStatus = Literal["suspected", "confirmed", "ruled_out"]
DiagnosisSource = Literal["clinician", "copy_forward"]


class DiagnosisWrite(CamelModel):
    concept_public_id: str = Field(min_length=26, max_length=26)
    laterality: Laterality
    status: DiagnosisStatus
    is_primary: bool = False
    onset_date: date | None = None
    note: str | None = Field(default=None, max_length=400)
    sort_order: int = Field(default=0, ge=0, le=1000)
    source: DiagnosisSource = "clinician"


class DiagnosisFavoriteReplace(CamelModel):
    concept_public_ids: list[str] = Field(default_factory=list, max_length=40)
