"""Otology read models. Concept displays are resolved for the request locale."""

from __future__ import annotations

from datetime import date, datetime

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class OtologyStructureRead(CamelModel):
    body_site: CodeableConcept
    laterality: str
    status: str
    finding: CodeableConcept
    map_region_code: str | None


class OfficeProcedureRead(CamelModel):
    subtype: str
    payload: dict[str, str | None]
    removal_due_date: date | None


class EarDeviceRead(CamelModel):
    public_id: str
    version: int
    laterality: str
    device_type: str
    tube_model: str | None
    status: str
    inserted_at: date
    removed_at: date | None
    next_check_due: date
    complication: str | None
    inserted_procedure_id: str | None


class OtologyExamRead(CamelModel):
    public_id: str
    version: int
    procedure_id: str
    procedure_status: str
    procedure_code: str
    patient_id: str
    encounter_id: str | None
    performed_at: datetime
    laterality: str
    anesthesia: str
    setting: str
    instrument: str | None
    indication_text: str | None
    tolerance: str | None
    method: str
    weber: str | None
    rinne_right: str | None
    rinne_left: str | None
    fork_frequency_hz: int | None
    mobility_right: str | None
    mobility_left: str | None
    structures: list[OtologyStructureRead]
    procedure: OfficeProcedureRead | None
    devices: list[EarDeviceRead]
    conclusion_text: str | None
    created_at: datetime
    updated_at: datetime
