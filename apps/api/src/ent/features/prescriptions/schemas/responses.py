"""Prescription read models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class SafetyAlertRead(CamelModel):
    code: str
    severity: str
    item_index: int | None = None


class SafetyOverrideRead(CamelModel):
    code: str
    reason: str
    user_public_id: str
    at: str


class FlagRead(CamelModel):
    code: str
    detail: dict[str, str]


class CalculationRead(CamelModel):
    code: str
    value: str
    unit: str | None
    formula: str
    version: str
    reference: str
    flags: list[FlagRead]
    inputs: dict[str, str]


class DrugFormRead(CamelModel):
    public_id: str
    form: str
    strength_value: Decimal | None
    strength_unit: str | None
    concentration_mg_per_ml: Decimal | None
    package_description: str | None


class DrugRead(CamelModel):
    public_id: str
    code: str
    inn_name: str
    atc_code: str | None
    drug_class: str | None
    is_ototoxic: bool
    is_anticoagulant: bool
    pregnancy_category: str | None
    concept: CodeableConcept | None
    forms: list[DrugFormRead]


class FormularyEntryRead(CamelModel):
    public_id: str
    brand_name: str
    is_available: bool
    local_code: str | None
    price: Decimal | None
    currency_code: str | None
    notes: str | None
    dosing_rules: dict[str, object] | None
    version: int
    drug: DrugRead


class PrescriptionItemRead(CamelModel):
    public_id: str
    free_text_name: str | None
    drug_code: str | None
    drug_inn: str | None
    drug_class: str | None
    form: str | None
    concept: CodeableConcept | None
    dose_amount: Decimal | None
    dose_unit: str | None
    volume_ml: Decimal | None
    route: str
    frequency_per_day: int
    interval_hours: int | None
    duration_days: int
    quantity: str | None
    instructions_text: str | None
    taper_schedule: list[dict[str, object]] | None
    is_renewable: bool
    substitution_allowed: bool
    safety_overrides: list[SafetyOverrideRead]
    sort_order: int
    dosing_engine_version: str | None


class PrescriptionRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str
    status: str
    locale: str
    is_pediatric: bool
    weight_kg: Decimal | None
    issued_at: datetime | None
    notes: str | None
    version: int
    safety_alerts: list[SafetyAlertRead]
    items: list[PrescriptionItemRead]


class PrescriptionTemplateRead(CamelModel):
    public_id: str
    code: str
    name_key: str
    is_pediatric: bool
    complaint_concept_ids: list[str]
    items: list[dict[str, object]]
    version: int
