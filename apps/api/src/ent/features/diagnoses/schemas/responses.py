"""Diagnosis read models."""

from __future__ import annotations

from datetime import date

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class DiagnosisRead(CamelModel):
    public_id: str
    concept: CodeableConcept
    laterality: str
    status: str
    is_primary: bool
    onset_date: date | None = None
    note: str | None = None
    sort_order: int
    source: str
    promoted_problem_public_id: str | None = None
    derived_from_public_id: str | None = None


class DiagnosisFavoriteRead(CamelModel):
    concept: CodeableConcept
    sort_order: int
