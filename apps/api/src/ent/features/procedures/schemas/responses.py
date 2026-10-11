"""Procedure read models. Integer ids never leave the process."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class ProcedureAddendumRead(CamelModel):
    public_id: str
    author_public_id: str
    author_display_name: str
    body: str
    created_at: datetime


class ProcedureRecordRead(CamelModel):
    public_id: str
    patient_id: str
    patient_display_name: str
    encounter_id: str | None
    procedure: CodeableConcept
    performed_at: datetime
    performed_by_id: str
    performed_by_display_name: str
    laterality: str
    anesthesia: str
    setting: str
    instrument: str | None
    indication_text: str | None
    tolerance: str | None
    complication: CodeableConcept | None
    complication_note: str | None
    status: str
    signed_at: datetime | None
    signed_by_id: str | None
    signed_role: str | None
    locked_hash: str | None
    version: int
    created_at: datetime
    updated_at: datetime
    addenda: list[ProcedureAddendumRead]
