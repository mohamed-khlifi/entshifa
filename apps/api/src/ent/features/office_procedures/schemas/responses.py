"""Office-procedure read models. Displays come from concept translations."""

from __future__ import annotations

from datetime import date, datetime

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept
from ent.features.office_procedures.schemas.requests import ShortProcedureWrite


class OfficeProcedureRead(CamelModel):
    public_id: str
    version: int
    procedure_id: str
    procedure_status: str
    procedure: CodeableConcept
    patient_id: str
    encounter_id: str | None
    performed_at: datetime
    laterality: str
    anesthesia: str
    tolerance: str | None
    indication_text: str | None
    detail: ShortProcedureWrite
    removal_due_date: date | None
    result_due_date: date | None
    created_at: datetime
    updated_at: datetime
