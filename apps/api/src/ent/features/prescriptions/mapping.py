"""Map prescription rows to read models."""

from __future__ import annotations

from typing import Any

from ent.core.schemas.common import CodeableConcept
from ent.engines.results import CalculationResult
from ent.features.prescriptions.models import (
    Drug,
    DrugForm,
    FormularyEntry,
    Prescription,
    PrescriptionItem,
    PrescriptionTemplate,
)
from ent.features.prescriptions.schemas.responses import (
    CalculationRead,
    DrugFormRead,
    DrugRead,
    FlagRead,
    FormularyEntryRead,
    PrescriptionItemRead,
    PrescriptionRead,
    PrescriptionTemplateRead,
    SafetyAlertRead,
    SafetyOverrideRead,
)

Labels = dict[int, tuple[str, str, str | None]]


def _concept(concept_id: int | None, labels: Labels) -> CodeableConcept | None:
    if concept_id is None or concept_id not in labels:
        return None
    public_id, code, display = labels[concept_id]
    return CodeableConcept(concept_id=public_id, code=code, display=display)


def _form(row: DrugForm) -> DrugFormRead:
    return DrugFormRead(
        public_id=row.public_id,
        form=row.form,
        strength_value=row.strength_value,
        strength_unit=row.strength_unit,
        concentration_mg_per_ml=row.concentration_mg_per_ml,
        package_description=row.package_description,
    )


def drug_read(
    row: Drug, labels: Labels, forms: list[DrugForm] | None = None
) -> DrugRead:
    chosen = forms if forms is not None else list(row.forms)
    return DrugRead(
        public_id=row.public_id,
        code=row.code,
        inn_name=row.inn_name,
        atc_code=row.atc_code,
        drug_class=row.drug_class,
        is_ototoxic=bool(row.is_ototoxic),
        is_anticoagulant=bool(row.is_anticoagulant),
        pregnancy_category=row.pregnancy_category,
        concept=_concept(
            int(row.concept_id) if row.concept_id is not None else None, labels
        ),
        forms=[_form(item) for item in chosen if item.deleted_at is None],
    )


def _camel_key(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def camelize(value: object) -> object:
    """CamelCase keys for JSON documents stored in snake_case."""

    if isinstance(value, list):
        return [camelize(item) for item in value]
    if isinstance(value, dict):
        return {_camel_key(str(key)): camelize(item) for key, item in value.items()}
    return value


def formulary_read(row: FormularyEntry, labels: Labels) -> FormularyEntryRead:
    drug = row.drug_form.drug
    return FormularyEntryRead(
        public_id=row.public_id,
        brand_name=row.brand_name,
        is_available=bool(row.is_available),
        local_code=row.local_code,
        price=row.price,
        currency_code=row.currency_code,
        notes=row.notes,
        dosing_rules=camelize(row.dosing_rules) if row.dosing_rules else None,  # type: ignore[arg-type]
        version=int(row.version),
        drug=drug_read(drug, labels, forms=[row.drug_form]),
    )


def _overrides(raw: list[Any] | None) -> list[SafetyOverrideRead]:
    overrides: list[SafetyOverrideRead] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        overrides.append(
            SafetyOverrideRead(
                code=str(item["code"]),
                reason=str(item["reason"]),
                user_public_id=str(item["user_public_id"]),
                at=str(item["at"]),
            )
        )
    return overrides


def _alerts(raw: object) -> list[SafetyAlertRead]:
    if not isinstance(raw, list):
        return []
    alerts: list[SafetyAlertRead] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        index = item.get("item_index")
        alerts.append(
            SafetyAlertRead(
                code=str(item["code"]),
                severity=str(item["severity"]),
                item_index=None if index is None else int(index),
            )
        )
    return alerts


def item_read(row: PrescriptionItem, labels: Labels) -> PrescriptionItemRead:
    form = row.drug_form
    drug = form.drug if form is not None else None
    concept_id = int(drug.concept_id) if drug is not None and drug.concept_id else None
    return PrescriptionItemRead(
        public_id=row.public_id,
        free_text_name=row.free_text_name,
        drug_code=None if drug is None else drug.code,
        drug_inn=None if drug is None else drug.inn_name,
        drug_class=None if drug is None else drug.drug_class,
        form=None if form is None else form.form,
        concept=_concept(concept_id, labels),
        dose_amount=row.dose_amount,
        dose_unit=row.dose_unit,
        volume_ml=row.volume_ml,
        route=row.route,
        frequency_per_day=int(row.frequency_per_day),
        interval_hours=None if row.interval_hours is None else int(row.interval_hours),
        duration_days=int(row.duration_days),
        quantity=row.quantity,
        instructions_text=row.instructions_text,
        taper_schedule=row.taper_schedule,
        is_renewable=bool(row.is_renewable),
        substitution_allowed=bool(row.substitution_allowed),
        safety_overrides=_overrides(row.safety_overrides),
        sort_order=int(row.sort_order),
        dosing_engine_version=row.dosing_engine_version,
    )


def prescription_read(
    row: Prescription,
    *,
    patient_public_id: str,
    encounter_public_id: str,
    labels: Labels,
    alerts: list[dict[str, Any]] | None = None,
) -> PrescriptionRead:
    return PrescriptionRead(
        public_id=row.public_id,
        patient_public_id=patient_public_id,
        encounter_public_id=encounter_public_id,
        status=row.status,
        locale=row.locale,
        is_pediatric=bool(row.is_pediatric),
        weight_kg=row.weight_kg_at_issue,
        issued_at=row.issued_at,
        notes=row.notes,
        version=int(row.version),
        safety_alerts=_alerts(row.safety_alerts if alerts is None else alerts),
        items=[
            item_read(item, labels) for item in row.items if item.deleted_at is None
        ],
    )


def template_read(row: PrescriptionTemplate) -> PrescriptionTemplateRead:
    complaints = (
        row.complaint_concept_ids if isinstance(row.complaint_concept_ids, list) else []
    )
    items = row.items if isinstance(row.items, list) else []
    return PrescriptionTemplateRead(
        public_id=row.public_id,
        code=row.code,
        name_key=row.name_key,
        is_pediatric=bool(row.is_pediatric),
        complaint_concept_ids=[str(item) for item in complaints],
        items=[item for item in items if isinstance(item, dict)],
        version=int(row.version),
    )


def calculation_read(result: CalculationResult) -> CalculationRead:
    return CalculationRead(
        code=result.code,
        value=result.value,
        unit=result.unit,
        formula=result.formula,
        version=result.version,
        reference=result.reference,
        inputs=dict(result.inputs),
        flags=[
            FlagRead(code=flag.code, detail=dict(flag.detail)) for flag in result.flags
        ],
    )
