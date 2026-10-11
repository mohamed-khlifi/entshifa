"""Prescription and formulary ORM models (architecture section 25.11 / P2-08)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import (
    ClinicalRecordMixin,
    GlobalRecordMixin,
    SurrogatePkMixin,
    TimestampMixin,
)
from ent.core.db.mysql_types import datetime6, mysql_json, unsigned_bigint
from ent.core.db.types import ULIDType
from ent.features.prescriptions.constants import (
    DRUG_FORMS,
    PREGNANCY_CATEGORIES,
    PRESCRIPTION_STATUSES,
    ROUTES,
)
from ent.features.terminology.models import Concept

_FORM_SQL = ",".join(f"'{value}'" for value in DRUG_FORMS)
_ROUTE_SQL = ",".join(f"'{value}'" for value in ROUTES)
_STATUS_SQL = ",".join(f"'{value}'" for value in PRESCRIPTION_STATUSES)
_PREGNANCY_SQL = ",".join(f"'{value}'" for value in PREGNANCY_CATEGORIES)


class Drug(GlobalRecordMixin, Base):
    """Global drug identity. Dosing rules live on the clinic formulary, not here."""

    __tablename__ = "drug"
    __audit_writes__ = True
    __table_args__ = (
        UniqueConstraint("code", name="uq_drug__code"),
        CheckConstraint(
            f"pregnancy_category IS NULL OR pregnancy_category IN ({_PREGNANCY_SQL})",
            name="ck_drug__pregnancy_category",
        ),
        Index("ix_drug__drug_class", "drug_class"),
    )

    code: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    inn_name: Mapped[str] = mapped_column(String(160), nullable=False)
    atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    drug_class: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_ototoxic: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    is_anticoagulant: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    pregnancy_category: Mapped[str | None] = mapped_column(String(10), nullable=True)
    concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )

    forms: Mapped[list[DrugForm]] = relationship(back_populates="drug")
    concept: Mapped[Concept | None] = relationship()


class DrugForm(GlobalRecordMixin, Base):
    __tablename__ = "drug_form"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(f"form IN ({_FORM_SQL})", name="ck_drug_form__form"),
        CheckConstraint(
            "strength_value IS NULL OR strength_value > 0",
            name="ck_drug_form__strength_value",
        ),
        CheckConstraint(
            "concentration_mg_per_ml IS NULL OR concentration_mg_per_ml > 0",
            name="ck_drug_form__concentration",
        ),
        Index("ix_drug_form__drug_id", "drug_id"),
    )

    drug_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("drug.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    form: Mapped[str] = mapped_column(String(40), nullable=False)
    strength_value: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    strength_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    concentration_mg_per_ml: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    package_description: Mapped[str | None] = mapped_column(String(120), nullable=True)

    drug: Mapped[Drug] = relationship(back_populates="forms")


class FormularyEntry(ClinicalRecordMixin, Base):
    """Clinic-editable product and dosing rule. The engine never hardcodes this."""

    __tablename__ = "formulary_entry"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            "price IS NULL OR (currency_code IS NOT NULL AND price >= 0)",
            name="ck_formulary_entry__price",
        ),
        UniqueConstraint(
            "clinic_id",
            "drug_form_id",
            name="uq_formulary_entry__clinic_id__drug_form_id",
        ),
        Index(
            "ix_formulary_entry__clinic_id__is_available",
            "clinic_id",
            "is_available",
        ),
    )

    drug_form_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("drug_form.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    brand_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    local_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dosing_rules: Mapped[dict[str, Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )

    drug_form: Mapped[DrugForm] = relationship()


class Prescription(ClinicalRecordMixin, Base):
    __tablename__ = "prescription"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_SQL})",
            name="ck_prescription__status",
        ),
        CheckConstraint(
            "weight_kg_at_issue IS NULL OR weight_kg_at_issue > 0",
            name="ck_prescription__weight",
        ),
        Index(
            "ix_prescription__clinic_id__patient_id__issued_at",
            "clinic_id",
            "patient_id",
            "issued_at",
        ),
        Index(
            "ix_prescription__clinic_id__encounter_id",
            "clinic_id",
            "encounter_id",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    encounter_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    prescriber_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    issued_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("document.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_kg_at_issue: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    is_pediatric: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    safety_alerts: Mapped[list[Any] | None] = mapped_column(mysql_json(), nullable=True)

    items: Mapped[list[PrescriptionItem]] = relationship(
        back_populates="prescription",
        order_by="PrescriptionItem.sort_order",
    )


class PrescriptionItem(ClinicalRecordMixin, Base):
    __tablename__ = "prescription_item"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            "(drug_form_id IS NOT NULL AND free_text_name IS NULL) "
            "OR (drug_form_id IS NULL AND free_text_name IS NOT NULL)",
            name="ck_prescription_item__identity",
        ),
        CheckConstraint(
            "dose_amount IS NULL OR dose_amount > 0",
            name="ck_prescription_item__dose_amount",
        ),
        CheckConstraint(
            f"route IN ({_ROUTE_SQL})",
            name="ck_prescription_item__route",
        ),
        CheckConstraint(
            "frequency_per_day >= 1",
            name="ck_prescription_item__frequency",
        ),
        CheckConstraint(
            "duration_days >= 1",
            name="ck_prescription_item__duration",
        ),
        Index(
            "ix_prescription_item__clinic_id__prescription_id__sort_order",
            "clinic_id",
            "prescription_id",
            "sort_order",
        ),
    )

    prescription_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("prescription.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    drug_form_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("drug_form.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    free_text_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    dose_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    volume_ml: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    route: Mapped[str] = mapped_column(String(30), nullable=False)
    frequency_per_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    interval_hours: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    duration_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(60), nullable=True)
    instructions_text: Mapped[str | None] = mapped_column(String(400), nullable=True)
    taper_schedule: Mapped[list[Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    is_renewable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    substitution_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    safety_overrides: Mapped[list[Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    dosing_engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    prescription: Mapped[Prescription] = relationship(back_populates="items")
    drug_form: Mapped[DrugForm | None] = relationship()


class PrescriptionTemplate(ClinicalRecordMixin, Base):
    __tablename__ = "prescription_template"
    __audit_writes__ = True
    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "code",
            name="uq_prescription_template__clinic_id__code",
        ),
        Index(
            "ix_prescription_template__clinic_id__user_id",
            "clinic_id",
            "user_id",
        ),
    )

    user_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    name_key: Mapped[str] = mapped_column(String(80), nullable=False)
    complaint_concept_ids: Mapped[list[Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    items: Mapped[list[Any]] = mapped_column(mysql_json(), nullable=False)
    is_pediatric: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )


class CalculationResultRow(ClinicalRecordMixin, Base):
    """Stored calculator output so a later version can still be reproduced."""

    __tablename__ = "calculation_result"
    __audit_writes__ = True
    __table_args__ = (
        Index(
            "ix_calculation_result__clinic_id__patient_id__computed_at",
            "clinic_id",
            "patient_id",
            "computed_at",
        ),
        Index(
            "ix_calculation_result__clinic_id__calculator_code",
            "clinic_id",
            "calculator_code",
        ),
        Index(
            "ix_calc_result__clinic_procedure",
            "clinic_id",
            "procedure_record_id",
        ),
    )

    patient_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    procedure_record_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "procedure_record.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_calculation_result__procedure",
        ),
        nullable=True,
    )
    calculator_code: Mapped[str] = mapped_column(String(60), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
    value: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    flags: Mapped[list[Any]] = mapped_column(mysql_json(), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    computed_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )


class PrescriptionRequestIdempotency(SurrogatePkMixin, TimestampMixin, Base):
    """Idempotency-Key memory for prescription creates."""

    __tablename__ = "prescription_request_idempotency"
    __table_args__ = (
        Index(
            "uq_rx_idempotency__clinic_id__idempotency_key",
            "clinic_id",
            "idempotency_key",
            unique=True,
        ),
    )

    public_id: Mapped[str] = mapped_column(
        ULIDType(),
        nullable=False,
        unique=True,
    )
    clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(80, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    request_hash: Mapped[str] = mapped_column(
        String(64, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_public_id: Mapped[str] = mapped_column(ULIDType(), nullable=False)
