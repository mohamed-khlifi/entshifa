"""Prescription write models."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ent.core.schemas.base import CamelModel

Route = Literal["oral", "nasal", "otic", "topical", "injection"]
OverrideCode = Literal[
    "prescription.allergy_conflict",
    "prescription.dose_above_maximum",
]


class SafetyOverrideWrite(CamelModel):
    code: OverrideCode
    reason: str = Field(min_length=1, max_length=400)


class TaperWrite(CamelModel):
    start_mg: Decimal = Field(gt=0)
    step_mg: Decimal = Field(gt=0)
    days_per_step: int = Field(ge=1, le=31)
    minimum_mg: Decimal = Field(ge=0, default=Decimal("0"))


class AgeCapWrite(CamelModel):
    max_completed_years: int = Field(ge=0, le=120)
    max_mg_per_day: Decimal = Field(gt=0)


class IndicationWrite(CamelModel):
    mg_per_kg_per_day: Decimal | None = Field(default=None, gt=0)
    doses_per_day: int | None = Field(default=None, ge=1, le=24)
    max_mg_per_day: Decimal | None = Field(default=None, gt=0)
    default_duration_days: int | None = Field(default=None, ge=1, le=3650)


class DosingRuleWrite(CamelModel):
    """Clinic-authored rule. Numbers are stored as exact decimal strings."""

    mg_per_kg_per_day: Decimal | None = Field(default=None, gt=0)
    doses_per_day: int | None = Field(default=None, ge=1, le=24)
    max_mg_per_day: Decimal | None = Field(default=None, gt=0)
    default_duration_days: int | None = Field(default=None, ge=1, le=3650)
    age_caps: list[AgeCapWrite] = Field(default_factory=list)
    indications: dict[str, IndicationWrite] = Field(default_factory=dict)
    taper: TaperWrite | None = None

    @field_validator("indications")
    @classmethod
    def indication_codes(
        cls, value: dict[str, IndicationWrite]
    ) -> dict[str, IndicationWrite]:
        for code in value:
            if not code.replace("_", "").isalnum() or code != code.lower():
                msg = "indication_code"
                raise ValueError(msg)
        return value


class PrescriptionItemWrite(CamelModel):
    formulary_entry_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    free_text_name: str | None = Field(default=None, min_length=1, max_length=160)
    dose_amount: Decimal | None = Field(default=None, gt=0, le=Decimal("100000"))
    dose_unit: str | None = Field(default=None, min_length=1, max_length=20)
    route: Route
    frequency_per_day: int = Field(ge=1, le=24)
    interval_hours: int | None = Field(default=None, ge=1, le=168)
    duration_days: int = Field(ge=1, le=3650)
    quantity: str | None = Field(default=None, max_length=60)
    instructions_text: str | None = Field(default=None, max_length=400)
    is_renewable: bool = False
    substitution_allowed: bool = True
    sort_order: int = Field(default=0, ge=0, le=200)
    calculate_from_formulary: bool = False
    indication_code: str | None = Field(default=None, max_length=60)
    taper: TaperWrite | None = None
    use_formulary_taper: bool = False
    safety_overrides: list[SafetyOverrideWrite] = Field(default_factory=list)

    @model_validator(mode="after")
    def one_identity(self) -> PrescriptionItemWrite:
        has_formulary = self.formulary_entry_public_id is not None
        has_text = self.free_text_name is not None
        if has_formulary == has_text:
            msg = "item_identity"
            raise ValueError(msg)
        if self.calculate_from_formulary and not has_formulary:
            msg = "calculated_dose_needs_formulary"
            raise ValueError(msg)
        if self.use_formulary_taper and not has_formulary:
            msg = "formulary_taper_needs_formulary"
            raise ValueError(msg)
        if self.taper is not None and self.use_formulary_taper:
            msg = "taper_source"
            raise ValueError(msg)
        if not self.calculate_from_formulary and (
            self.dose_amount is None or self.dose_unit is None
        ):
            msg = "dose_required"
            raise ValueError(msg)
        return self


class PrescriptionCreate(CamelModel):
    encounter_public_id: str = Field(min_length=26, max_length=26)
    locale: str = Field(min_length=2, max_length=10)
    is_pediatric: bool = False
    weight_kg: Decimal | None = Field(default=None, gt=0, le=Decimal("999.99"))
    notes: str | None = None
    items: list[PrescriptionItemWrite] = Field(min_length=1, max_length=40)


class PrescriptionUpdate(CamelModel):
    version: int = Field(ge=1)
    locale: str | None = Field(default=None, min_length=2, max_length=10)
    is_pediatric: bool | None = None
    weight_kg: Decimal | None = Field(default=None, gt=0, le=Decimal("999.99"))
    notes: str | None = None
    items: list[PrescriptionItemWrite] | None = Field(
        default=None, min_length=1, max_length=40
    )


class SafetyCheckRequest(CamelModel):
    is_pediatric: bool = False
    weight_kg: Decimal | None = Field(default=None, gt=0, le=Decimal("999.99"))
    items: list[PrescriptionItemWrite] = Field(min_length=1, max_length=40)


class PediatricDoseRequest(CamelModel):
    formulary_entry_public_id: str = Field(min_length=26, max_length=26)
    weight_kg: Decimal = Field(gt=0, le=Decimal("999.99"))
    indication_code: str | None = Field(default=None, max_length=60)


class TaperRequest(CamelModel):
    start_mg: Decimal = Field(gt=0)
    step_mg: Decimal = Field(gt=0)
    days_per_step: int = Field(ge=1, le=31)
    minimum_mg: Decimal = Field(ge=0, default=Decimal("0"))


class FormularyEntryCreate(CamelModel):
    drug_form_public_id: str = Field(min_length=26, max_length=26)
    brand_name: str = Field(min_length=1, max_length=120)
    is_available: bool = True
    local_code: str | None = Field(default=None, max_length=40)
    price: Decimal | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=255)
    dosing_rules: DosingRuleWrite | None = None

    @model_validator(mode="after")
    def price_has_currency(self) -> FormularyEntryCreate:
        if self.price is not None and self.currency_code is None:
            msg = "currency_required"
            raise ValueError(msg)
        if self.currency_code is not None:
            self.currency_code = self.currency_code.upper()
        return self


class FormularyEntryUpdate(CamelModel):
    version: int = Field(ge=1)
    brand_name: str | None = Field(default=None, min_length=1, max_length=120)
    is_available: bool | None = None
    local_code: str | None = Field(default=None, max_length=40)
    price: Decimal | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=255)
    dosing_rules: DosingRuleWrite | None = None


class PrescriptionTemplateCreate(CamelModel):
    code: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9_]+$")
    name_key: str = Field(
        min_length=3,
        max_length=80,
        pattern=r"^[a-z0-9]+(\.[a-z0-9_]+)+$",
    )
    is_pediatric: bool = False
    complaint_concept_ids: list[str] = Field(default_factory=list, max_length=20)
    items: list[PrescriptionItemWrite] = Field(min_length=1, max_length=40)


def dosing_rules_document(rule: DosingRuleWrite) -> dict[str, object]:
    """Exact decimal strings so MySQL JSON never stores a binary float."""

    def indication(item: IndicationWrite) -> dict[str, object]:
        payload: dict[str, object] = {}
        if item.mg_per_kg_per_day is not None:
            payload["mg_per_kg_per_day"] = format(item.mg_per_kg_per_day, "f")
        if item.doses_per_day is not None:
            payload["doses_per_day"] = item.doses_per_day
        if item.max_mg_per_day is not None:
            payload["max_mg_per_day"] = format(item.max_mg_per_day, "f")
        if item.default_duration_days is not None:
            payload["default_duration_days"] = item.default_duration_days
        return payload

    document: dict[str, object] = {}
    if rule.mg_per_kg_per_day is not None:
        document["mg_per_kg_per_day"] = format(rule.mg_per_kg_per_day, "f")
    if rule.doses_per_day is not None:
        document["doses_per_day"] = rule.doses_per_day
    if rule.max_mg_per_day is not None:
        document["max_mg_per_day"] = format(rule.max_mg_per_day, "f")
    if rule.default_duration_days is not None:
        document["default_duration_days"] = rule.default_duration_days
    if rule.age_caps:
        document["age_caps"] = [
            {
                "max_completed_years": cap.max_completed_years,
                "max_mg_per_day": format(cap.max_mg_per_day, "f"),
            }
            for cap in rule.age_caps
        ]
    if rule.indications:
        document["indications"] = {
            code: indication(item) for code, item in rule.indications.items()
        }
    if rule.taper is not None:
        document["taper"] = {
            "start_mg": format(rule.taper.start_mg, "f"),
            "step_mg": format(rule.taper.step_mg, "f"),
            "days_per_step": rule.taper.days_per_step,
            "minimum_mg": format(rule.taper.minimum_mg, "f"),
        }
    return document
