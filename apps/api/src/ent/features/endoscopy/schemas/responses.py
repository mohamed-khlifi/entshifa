"""Endoscopy read models. Concept displays are resolved for the request locale."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class LundKennedySideRead(CamelModel):
    polyps: int
    edema: int
    discharge: int
    scarring: int
    crusting: int
    total: int


class EndoscopyStructureRead(CamelModel):
    body_site: CodeableConcept
    laterality: str
    status: str
    finding: CodeableConcept


class ScoreStampRead(CamelModel):
    code: str
    version: str
    value: str
    unit: str | None
    reference: str
    formula: str


class EndoscopyExamRead(CamelModel):
    public_id: str
    version: int
    procedure_id: str
    procedure_status: str
    patient_id: str
    encounter_id: str | None
    performed_at: datetime
    laterality: str
    anesthesia: str
    setting: str
    instrument: str | None
    indication_text: str | None
    tolerance: str | None
    scope_type: str
    decongestant_used: bool
    lund_kennedy_right: LundKennedySideRead
    lund_kennedy_left: LundKennedySideRead
    lund_kennedy_total: int
    modified_lk_right: int
    modified_lk_left: int
    modified_lk_total: int
    polyp_grade_right: int | None
    polyp_grade_left: int | None
    polyp_scale: str
    adenoid_obstruction_pct: int | None
    conclusion_text: str | None
    structures: list[EndoscopyStructureRead]
    scores: list[ScoreStampRead]
    created_at: datetime
    updated_at: datetime
