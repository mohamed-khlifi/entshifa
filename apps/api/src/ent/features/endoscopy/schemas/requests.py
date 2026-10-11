"""Endoscopy write payloads. Scores are computed; the client does not send totals."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality
from ent.features.endoscopy.constants import ScopeType, StructureStatus
from ent.features.procedures.constants import (
    AnesthesiaType,
    ProcedureSetting,
    ToleranceValue,
)

_NOTE = 10_000


class LundKennedySideWrite(CamelModel):
    polyps: int
    edema: int
    discharge: int
    scarring: int
    crusting: int


class EndoscopyStructureWrite(CamelModel):
    body_site_code: str = Field(min_length=1, max_length=60)
    laterality: Laterality
    status: StructureStatus
    finding_code: str = Field(min_length=1, max_length=60)


class _EndoscopyBody(CamelModel):
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime
    laterality: Laterality = Laterality.BILATERAL
    anesthesia: AnesthesiaType = "topical_spray"
    setting: ProcedureSetting = "office"
    instrument: str | None = Field(default=None, max_length=100)
    indication_text: str | None = Field(default=None, max_length=400)
    tolerance: ToleranceValue | None = None
    scope_type: ScopeType
    decongestant_used: bool = False
    structures: list[EndoscopyStructureWrite] = Field(default_factory=list)
    lund_kennedy_right: LundKennedySideWrite
    lund_kennedy_left: LundKennedySideWrite
    polyp_grade_right: int | None = None
    polyp_grade_left: int | None = None
    adenoid_obstruction_pct: int | None = None
    conclusion_text: str | None = Field(default=None, max_length=_NOTE)


class EndoscopyCreate(_EndoscopyBody):
    patient_public_id: str = Field(min_length=26, max_length=26)


class EndoscopyUpdate(_EndoscopyBody):
    version: int = Field(ge=1)
