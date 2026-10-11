"""Otology exam, office ear procedure, and ear-device registry (architecture §25.7)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import mysql_json, unsigned_bigint
from ent.features.office_procedures.constants import SHORT_OFFICE_SUBTYPES
from ent.features.otology.constants import (
    DEVICE_STATUSES,
    DEVICE_TYPES,
    EXAM_METHODS,
    MOBILITY_VALUES,
    OFFICE_SUBTYPES,
    RINNE_VALUES,
    TUBE_COMPLICATIONS,
    TUBE_MODELS,
    WEBER_VALUES,
)
from ent.features.otology.guard import install_otology_guards
from ent.features.procedures.models import ProcedureRecord


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


def _in(column: str, values: tuple[str, ...], *, nullable: bool) -> str:
    rendered = ",".join(f"'{value}'" for value in values)
    clause = f"{column} IN ({rendered})"
    if nullable:
        return f"{column} IS NULL OR {clause}"
    return clause


_LATERALITY = "'right','left','bilateral'"


class OtologyExam(ClinicalRecordMixin, Base):
    """Microscopy or otoscopy attached to one procedure record."""

    __tablename__ = "otology_exam"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in("method", EXAM_METHODS, nullable=False),
            name="ck_otology_exam__method",
        ),
        CheckConstraint(
            _in("weber", WEBER_VALUES, nullable=True),
            name="ck_otology_exam__weber",
        ),
        CheckConstraint(
            _in("rinne_right", RINNE_VALUES, nullable=True),
            name="ck_otology_exam__rinne_r",
        ),
        CheckConstraint(
            _in("rinne_left", RINNE_VALUES, nullable=True),
            name="ck_otology_exam__rinne_l",
        ),
        CheckConstraint(
            "fork_frequency_hz IS NULL OR fork_frequency_hz IN (256, 512)",
            name="ck_otology_exam__fork",
        ),
        CheckConstraint(
            _in("mobility_right", MOBILITY_VALUES, nullable=True),
            name="ck_otology_exam__mob_r",
        ),
        CheckConstraint(
            _in("mobility_left", MOBILITY_VALUES, nullable=True),
            name="ck_otology_exam__mob_l",
        ),
        Index("uq_otology_exam__procedure", "procedure_record_id", unique=True),
        Index(
            "ix_otology_exam__clinic_procedure",
            "clinic_id",
            "procedure_record_id",
        ),
    )

    procedure_record_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "procedure_record.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_otology_exam__procedure",
        ),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    weber: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rinne_right: Mapped[str | None] = mapped_column(String(10), nullable=True)
    rinne_left: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fork_frequency_hz: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    mobility_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobility_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    conclusion_text: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)

    procedure_record: Mapped[ProcedureRecord] = relationship(
        foreign_keys=[procedure_record_id],
        lazy="selectin",
    )


class OfficeProcedure(ClinicalRecordMixin, Base):
    """Subtype payload for an office procedure. Ear and short forms share this row."""

    __tablename__ = "office_procedure"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in("subtype", OFFICE_SUBTYPES + SHORT_OFFICE_SUBTYPES, nullable=False),
            name="ck_office_procedure__subtype",
        ),
        Index("uq_office_procedure__live", "live_procedure_id", unique=True),
        Index(
            "ix_office_procedure__clinic_procedure",
            "clinic_id",
            "procedure_record_id",
        ),
    )

    procedure_record_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "procedure_record.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_office_procedure__procedure",
        ),
        nullable=False,
    )
    subtype: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
    removal_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    live_procedure_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        Computed(
            "CASE WHEN deleted_at IS NULL THEN procedure_record_id ELSE NULL END",
            persisted=True,
        ),
    )
    procedure_record: Mapped[ProcedureRecord] = relationship(
        foreign_keys=[procedure_record_id],
        lazy="selectin",
    )


class EarDevice(ClinicalRecordMixin, Base):
    """Ventilation tube or mastoid cavity that must stay on the patient card."""

    __tablename__ = "ear_device"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IN ({_LATERALITY})",
            name="ck_ear_device__laterality",
        ),
        CheckConstraint(
            _in("device_type", DEVICE_TYPES, nullable=False),
            name="ck_ear_device__device_type",
        ),
        CheckConstraint(
            _in("status", DEVICE_STATUSES, nullable=False),
            name="ck_ear_device__status",
        ),
        CheckConstraint(
            _in("tube_model", TUBE_MODELS, nullable=True),
            name="ck_ear_device__tube_model",
        ),
        CheckConstraint(
            _in("complication", TUBE_COMPLICATIONS, nullable=True),
            name="ck_ear_device__complication",
        ),
        Index(
            "ix_ear_device__clinic_id__status__next_check_due",
            "clinic_id",
            "status",
            "next_check_due",
        ),
        Index(
            "ix_ear_device__clinic_id__patient_id",
            "clinic_id",
            "patient_id",
        ),
        Index(
            "ix_ear_device__clinic_inserted_procedure",
            "clinic_id",
            "inserted_procedure_id",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "patient.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_ear_device__patient",
        ),
        nullable=False,
    )
    laterality: Mapped[str] = mapped_column(String(10), nullable=False)
    device_type: Mapped[str] = mapped_column(String(40), nullable=False)
    inserted_at: Mapped[date] = mapped_column(Date, nullable=False)
    inserted_procedure_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "procedure_record.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_ear_device__inserted_procedure",
        ),
        nullable=True,
    )
    tube_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    removed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    complication: Mapped[str | None] = mapped_column(String(80), nullable=True)
    next_check_due: Mapped[date] = mapped_column(Date, nullable=False)


install_otology_guards(OtologyExam, OfficeProcedure)
