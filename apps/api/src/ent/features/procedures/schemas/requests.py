"""Procedure write payloads. Child exams add their own bodies later."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality
from ent.features.procedures.constants import (
    AnesthesiaType,
    ProcedureSetting,
    ToleranceValue,
)

_NOTE = 10_000


class ProcedureRecordCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    procedure_concept_public_id: str = Field(min_length=26, max_length=26)
    performed_at: datetime
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    laterality: Laterality = Laterality.NA
    anesthesia: AnesthesiaType = "none"
    setting: ProcedureSetting = "office"
    instrument: str | None = Field(default=None, max_length=100)
    indication_text: str | None = Field(default=None, max_length=400)
    tolerance: ToleranceValue | None = None
    complication_concept_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    complication_note: str | None = Field(default=None, max_length=_NOTE)


class ProcedureRecordUpdate(CamelModel):
    version: int = Field(ge=1)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    procedure_concept_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    laterality: Laterality | None = None
    anesthesia: AnesthesiaType | None = None
    setting: ProcedureSetting | None = None
    instrument: str | None = Field(default=None, max_length=100)
    indication_text: str | None = Field(default=None, max_length=400)
    tolerance: ToleranceValue | None = None
    complication_concept_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    complication_note: str | None = Field(default=None, max_length=_NOTE)


class ProcedureSign(CamelModel):
    role: str = Field(
        default="clinician",
        min_length=1,
        max_length=30,
        pattern=r"^[a-z][a-z0-9_]*$",
    )


class ProcedureAddendumCreate(CamelModel):
    body: str = Field(min_length=1, max_length=_NOTE)
