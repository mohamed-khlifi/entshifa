"""Scheduling ORM models (architecture §25.4 / P1-07)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint
from ent.features.scheduling.constants import APPOINTMENT_STATUSES

_STATUS_SQL = ",".join(f"'{value}'" for value in APPOINTMENT_STATUSES)


class AppointmentType(ClinicalRecordMixin, Base):
    __tablename__ = "appointment_type"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            "default_duration_min > 0 AND default_duration_min <= 480",
            name="ck_appointment_type__duration",
        ),
        Index(
            "uq_appointment_type__clinic_id__code",
            "clinic_id",
            "code",
            unique=True,
        ),
    )

    code: Mapped[str] = mapped_column(
        String(40, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    name_key: Mapped[str] = mapped_column(String(80), nullable=False)
    default_duration_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    color: Mapped[str] = mapped_column(String(12), nullable=False)
    requires_room: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )


class Appointment(ClinicalRecordMixin, Base):
    __tablename__ = "appointment"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_SQL})",
            name="ck_appointment__status",
        ),
        CheckConstraint("ends_at > starts_at", name="ck_appointment__time_range"),
        Index(
            "ix_appointment__clinic_id__user_id__starts_at",
            "clinic_id",
            "user_id",
            "starts_at",
        ),
        Index(
            "ix_appointment__clinic_id__patient_id__starts_at",
            "clinic_id",
            "patient_id",
            "starts_at",
        ),
        Index(
            "ix_appointment__clinic_id__status__starts_at",
            "clinic_id",
            "status",
            "starts_at",
        ),
    )

    site_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("site.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    appointment_type_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("appointment_type.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    room: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_from_recall_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )
    arrived_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(160), nullable=True)
