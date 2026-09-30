"""Patient registry ORM models (architecture §25.3 / P1-05)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin, SurrogatePkMixin, TimestampMixin
from ent.core.db.mysql_types import mysql_json, unsigned_bigint
from ent.core.db.types import ULIDType
from ent.features.patients.constants import (
    ALLERGY_CATEGORIES,
    ALLERGY_SEVERITIES,
    HISTORY_CATEGORIES,
    IDENTIFIER_TYPES,
    LATERALITY_VALUES,
    MEDICATION_SOURCES,
    PATIENT_FLAG_CODES,
    PROBLEM_STATUSES,
    SEX_VALUES,
)

_LATERALITY_SQL = ",".join(f"'{value}'" for value in LATERALITY_VALUES)


def _in_check(column: str, values: tuple[str, ...], *, nullable: bool = False) -> str:
    rendered = ",".join(f"'{value}'" for value in values)
    if nullable:
        return f"{column} IS NULL OR {column} IN ({rendered})"
    return f"{column} IN ({rendered})"


class Patient(ClinicalRecordMixin, Base):
    __tablename__ = "patient"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(_in_check("sex", SEX_VALUES), name="ck_patient__sex"),
        Index("ix_patient__clinic_id__name_normalized", "clinic_id", "name_normalized"),
        Index("ix_patient__clinic_id__phone_primary", "clinic_id", "phone_primary"),
        Index("ix_patient__clinic_id__birth_date", "clinic_id", "birth_date"),
        Index("uq_patient__clinic_id__mrn", "clinic_id", "mrn", unique=True),
        Index(
            "ft_patient__names",
            "first_name",
            "last_name",
            "first_name_alt",
            "last_name_alt",
            mysql_prefix="FULLTEXT",
        ),
    )

    mrn: Mapped[str] = mapped_column(
        String(32, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    first_name_alt: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name_alt: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name_normalized: Mapped[str] = mapped_column(String(190), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_date_is_estimated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    sex: Mapped[str] = mapped_column(String(10), nullable=False)
    preferred_locale: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_primary: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_secondary: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(190), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(160), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(160), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    noise_exposure: Mapped[str | None] = mapped_column(String(40), nullable=True)
    smoking_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    alcohol_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # FK to insurance_scheme deferred until that table exists.
    insurance_scheme_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(), nullable=True
    )
    insurance_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    referring_doctor_name: Mapped[str | None] = mapped_column(
        String(160), nullable=True
    )
    referring_doctor_phone: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    referring_doctor_email: Mapped[str | None] = mapped_column(
        String(190), nullable=True
    )
    referring_doctor_locale: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )
    guardian_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    guardian_relation: Mapped[str | None] = mapped_column(String(40), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(160), nullable=True
    )
    emergency_contact_phone: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    consent_sms: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    consent_email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    consent_teaching: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    is_deceased: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    deceased_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    identifiers: Mapped[list[PatientIdentifier]] = relationship(
        back_populates="patient",
    )
    allergies: Mapped[list[PatientAllergy]] = relationship(back_populates="patient")
    medications: Mapped[list[PatientMedication]] = relationship(
        back_populates="patient",
    )
    flags: Mapped[list[PatientFlag]] = relationship(back_populates="patient")
    problems: Mapped[list[PatientProblem]] = relationship(back_populates="patient")
    history_entries: Mapped[list[PatientHistory]] = relationship(
        back_populates="patient",
    )


class PatientIdentifier(ClinicalRecordMixin, Base):
    __tablename__ = "patient_identifier"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("type", IDENTIFIER_TYPES),
            name="ck_patient_identifier__type",
        ),
        Index(
            "ix_patient_identifier__clinic_id__patient_id",
            "clinic_id",
            "patient_id",
        ),
        Index(
            "ix_patient_identifier__clinic_id__type__value",
            "clinic_id",
            "type",
            "value",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[str] = mapped_column(String(80), nullable=False)
    issuing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="identifiers")


class PatientAllergy(ClinicalRecordMixin, Base):
    __tablename__ = "patient_allergy"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("category", ALLERGY_CATEGORIES),
            name="ck_patient_allergy__category",
        ),
        CheckConstraint(
            _in_check("severity", ALLERGY_SEVERITIES, nullable=True),
            name="ck_patient_allergy__severity",
        ),
        Index(
            "ix_patient_allergy__clinic_id__patient_id__is_active",
            "clinic_id",
            "patient_id",
            "is_active",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    substance_concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    reaction_concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="allergies")


class PatientMedication(ClinicalRecordMixin, Base):
    __tablename__ = "patient_medication"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("source", MEDICATION_SOURCES),
            name="ck_patient_medication__source",
        ),
        Index(
            "ix_patient_medication__clinic_id__patient_id__is_active",
            "clinic_id",
            "patient_id",
            "is_active",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # FK to drug deferred until the formulary table exists.
    drug_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    free_text_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    dose: Mapped[str | None] = mapped_column(String(60), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(60), nullable=True)
    route: Mapped[str | None] = mapped_column(String(30), nullable=True)
    started_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    stopped_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    is_anticoagulant: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    is_ototoxic: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="medications")


class PatientFlag(ClinicalRecordMixin, Base):
    """ENT safety alert. Structured, dated, and sourced — never free text."""

    __tablename__ = "patient_flag"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("flag_code", PATIENT_FLAG_CODES),
            name="ck_patient_flag__flag_code",
        ),
        CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY_SQL})",
            name="ck_patient_flag__laterality",
        ),
        Index(
            "ix_patient_flag__clinic_id__patient_id__ended_on",
            "clinic_id",
            "patient_id",
            "ended_on",
        ),
        Index(
            "ix_patient_flag__clinic_id__flag_code__ended_on",
            "clinic_id",
            "flag_code",
            "ended_on",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    flag_code: Mapped[str] = mapped_column(String(60), nullable=False)
    laterality: Mapped[str | None] = mapped_column(String(10), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    detail: Mapped[dict[str, Any] | None] = mapped_column(mysql_json(), nullable=True)
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_auto: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )

    patient: Mapped[Patient] = relationship(back_populates="flags")


class PatientProblem(ClinicalRecordMixin, Base):
    __tablename__ = "patient_problem"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IN ({_LATERALITY_SQL})",
            name="ck_patient_problem__laterality",
        ),
        CheckConstraint(
            _in_check("status", PROBLEM_STATUSES),
            name="ck_patient_problem__status",
        ),
        Index(
            "ix_patient_problem__clinic_id__patient_id__status",
            "clinic_id",
            "patient_id",
            "status",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    diagnosis_concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    laterality: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_patient_problem__first_encounter",
        ),
        nullable=True,
    )
    last_encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_patient_problem__last_encounter",
        ),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="problems")


class PatientHistory(ClinicalRecordMixin, Base):
    __tablename__ = "patient_history"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("category", HISTORY_CATEGORIES),
            name="ck_patient_history__category",
        ),
        CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY_SQL})",
            name="ck_patient_history__laterality",
        ),
        Index(
            "ix_patient_history__clinic_id__patient_id__category",
            "clinic_id",
            "patient_id",
            "category",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    free_text: Mapped[str | None] = mapped_column(String(400), nullable=True)
    laterality: Mapped[str | None] = mapped_column(String(10), nullable=True)
    occurred_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    occurred_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    detail: Mapped[dict[str, Any] | None] = mapped_column(mysql_json(), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="history_entries")


class PatientMergeLog(ClinicalRecordMixin, Base):
    __tablename__ = "patient_merge_log"
    __audit_writes__ = True
    __table_args__ = (
        Index("ix_patient_merge_log__clinic_id__created_at", "clinic_id", "created_at"),
    )

    surviving_patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    merged_patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    merged_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)


class PatientRequestIdempotency(SurrogatePkMixin, TimestampMixin, Base):
    """Stores Idempotency-Key results for patient creates (architecture §35)."""

    __tablename__ = "patient_request_idempotency"
    __table_args__ = (
        Index(
            "uq_patient_request_idempotency__clinic_id__idempotency_key",
            "clinic_id",
            "idempotency_key",
            unique=True,
        ),
    )

    public_id: Mapped[str] = mapped_column(ULIDType(), nullable=False, unique=True)
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
