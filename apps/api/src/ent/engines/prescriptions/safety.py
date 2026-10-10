"""Prescription safety checks. Thresholds arrive as inputs, not constants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

VERSION = "1.0.0"
REFERENCE = (
    "P2-08 safety checks. Allergy and a missing pediatric weight block. "
    "Ototoxic-with-hearing-loss, duplicate class, pregnancy, breastfeeding, "
    "and dose above the supplied maximum are reported here; "
    "the service decides which blocks accept an override."
)

_CAUTION = frozenset({"caution", "contraindicated"})
_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class SafetyItem:
    allergy_concept_ids: frozenset[str]
    drug_class: str | None
    is_ototoxic: bool
    pregnancy_category: str | None
    daily_dose_mg: Decimal | None
    max_daily_dose_mg: Decimal | None
    is_unstructured: bool


@dataclass(frozen=True, slots=True)
class SafetyInput:
    items: tuple[SafetyItem, ...]
    active_allergy_concept_ids: frozenset[str]
    active_medication_classes: frozenset[str]
    hearing_loss_on_problem_list: bool
    is_pregnant: bool
    is_breastfeeding: bool
    is_pediatric: bool
    weight_kg: Decimal | None


@dataclass(frozen=True, slots=True)
class SafetyAlert:
    code: str
    severity: str
    item_index: int | None


def check_safety(data: SafetyInput) -> tuple[SafetyAlert, ...]:
    """Return block and warning alerts. Does not apply overrides."""

    alerts: list[SafetyAlert] = []
    if data.is_pediatric and (data.weight_kg is None or data.weight_kg <= _ZERO):
        alerts.append(
            SafetyAlert(
                code="prescription.pediatric_weight_missing",
                severity="block",
                item_index=None,
            )
        )

    seen_classes = set(data.active_medication_classes)
    for index, item in enumerate(data.items):
        if item.is_unstructured:
            alerts.append(
                SafetyAlert(
                    code="prescription.unstructured_item",
                    severity="warning",
                    item_index=index,
                )
            )
            continue
        if item.allergy_concept_ids & data.active_allergy_concept_ids:
            alerts.append(
                SafetyAlert(
                    code="prescription.allergy_conflict",
                    severity="block",
                    item_index=index,
                )
            )
        if (
            item.daily_dose_mg is not None
            and item.max_daily_dose_mg is not None
            and item.daily_dose_mg > item.max_daily_dose_mg
        ):
            alerts.append(
                SafetyAlert(
                    code="prescription.dose_above_maximum",
                    severity="block",
                    item_index=index,
                )
            )
        if item.is_ototoxic and data.hearing_loss_on_problem_list:
            alerts.append(
                SafetyAlert(
                    code="prescription.ototoxic_with_hearing_loss",
                    severity="warning",
                    item_index=index,
                )
            )
        drug_class = (item.drug_class or "").strip()
        if drug_class and drug_class in seen_classes:
            alerts.append(
                SafetyAlert(
                    code="prescription.duplicate_class",
                    severity="warning",
                    item_index=index,
                )
            )
        if drug_class:
            seen_classes.add(drug_class)
        category = item.pregnancy_category or ""
        if data.is_pregnant and category in _CAUTION:
            alerts.append(
                SafetyAlert(
                    code="prescription.pregnancy_caution",
                    severity="warning",
                    item_index=index,
                )
            )
        # VERIFY: one pregnancy_category column covers lactation until a
        # dedicated lactation column exists (architecture section 25.11).
        if data.is_breastfeeding and category in _CAUTION:
            alerts.append(
                SafetyAlert(
                    code="prescription.breastfeeding_caution",
                    severity="warning",
                    item_index=index,
                )
            )
    return tuple(alerts)
