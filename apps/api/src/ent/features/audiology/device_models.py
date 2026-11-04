"""Hearing devices, pediatric audiology and OME tracking (P4-06 / architecture §25.8)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.mysql import JSON, MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint
from ent.features.audiology.constants import (
    CANDIDACY_KINDS,
    DIAGNOSTIC_ABR_RESULTS,
    EHDI_BENCHMARK_STATUSES,
    HEARING_DEVICE_STATUSES,
    HEARING_DEVICE_TYPES,
    INTERVENTION_TYPES,
    NEWBORN_SCREEN_RESULTS,
    OME_STATUSES,
)

if TYPE_CHECKING:
    from ent.features.audiology.models import Audiogram
    from ent.features.audiology.test_records import Tympanometry
    from ent.features.encounters.models import Encounter
    from ent.features.patients.models import Patient
    from ent.features.users.models import User

_EAR_SQL = "'right','left'"
_LATERALITY_SQL = "'right','left','bilateral'"
_DEVICE_TYPE_SQL = ",".join(f"'{value}'" for value in HEARING_DEVICE_TYPES)
_DEVICE_STATUS_SQL = ",".join(f"'{value}'" for value in HEARING_DEVICE_STATUSES)
_SCREEN_SQL = ",".join(f"'{value}'" for value in NEWBORN_SCREEN_RESULTS)
_ABR_SQL = ",".join(f"'{value}'" for value in DIAGNOSTIC_ABR_RESULTS)
_INTERVENTION_SQL = ",".join(f"'{value}'" for value in INTERVENTION_TYPES)
_BENCHMARK_SQL = ",".join(f"'{value}'" for value in EHDI_BENCHMARK_STATUSES)
_OME_STATUS_SQL = ",".join(f"'{value}'" for value in OME_STATUSES)
_CANDIDACY_SQL = ",".join(f"'{value}'" for value in CANDIDACY_KINDS)


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


class HearingDevice(ClinicalRecordMixin, Base):
    __tablename__ = "hearing_device"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(f"ear IN ({_EAR_SQL})", name="ck_hearing_device__ear"),
        CheckConstraint(
            f"device_type IN ({_DEVICE_TYPE_SQL})",
            name="ck_hearing_device__device_type",
        ),
        CheckConstraint(
            f"status IN ({_DEVICE_STATUS_SQL})",
            name="ck_hearing_device__status",
        ),
        CheckConstraint(
            "daily_use_hours IS NULL OR (daily_use_hours >= 0 AND daily_use_hours <= 24)",
            name="ck_hearing_device__daily_use_hours",
        ),
        CheckConstraint(
            "satisfaction IS NULL OR (satisfaction >= 0 AND satisfaction <= 10)",
            name="ck_hearing_device__satisfaction",
        ),
        Index(
            "ix_hearing_device__clinic_id__patient_id__fitted_on",
            "clinic_id",
            "patient_id",
            text("fitted_on DESC"),
        ),
        Index(
            "ix_hearing_device__clinic_id__status__warranty_end",
            "clinic_id",
            "status",
            "warranty_end",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    ear: Mapped[str] = mapped_column(String(5), nullable=False)
    device_type: Mapped[str] = mapped_column(String(30), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(60), nullable=True)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    serial: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fitted_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    fitted_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    warranty_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_programmed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    battery_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    daily_use_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    satisfaction: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    aided_thresholds: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    surgeon: Mapped[str | None] = mapped_column(String(120), nullable=True)
    surgery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    electrode_array: Mapped[str | None] = mapped_column(String(80), nullable=True)
    implant_activation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mapping_dates: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    complications: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mri_conditions: Mapped[str | None] = mapped_column(String(160), nullable=True)
    notes: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")


class PediatricAudiologyRecord(ClinicalRecordMixin, Base):
    __tablename__ = "pediatric_audiology_record"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"screen_result_right IS NULL OR screen_result_right IN ({_SCREEN_SQL})",
            name="ck_pediatric_audiology__screen_r",
        ),
        CheckConstraint(
            f"screen_result_left IS NULL OR screen_result_left IN ({_SCREEN_SQL})",
            name="ck_pediatric_audiology__screen_l",
        ),
        CheckConstraint(
            f"rescreen_result_right IS NULL OR rescreen_result_right IN ({_SCREEN_SQL})",
            name="ck_pediatric_audiology__rescreen_r",
        ),
        CheckConstraint(
            f"rescreen_result_left IS NULL OR rescreen_result_left IN ({_SCREEN_SQL})",
            name="ck_pediatric_audiology__rescreen_l",
        ),
        CheckConstraint(
            f"diagnostic_abr_result_right IS NULL OR diagnostic_abr_result_right IN ({_ABR_SQL})",
            name="ck_pediatric_audiology__abr_r",
        ),
        CheckConstraint(
            f"diagnostic_abr_result_left IS NULL OR diagnostic_abr_result_left IN ({_ABR_SQL})",
            name="ck_pediatric_audiology__abr_l",
        ),
        CheckConstraint(
            f"intervention_type IS NULL OR intervention_type IN ({_INTERVENTION_SQL})",
            name="ck_pediatric_audiology__intervention_type",
        ),
        CheckConstraint(
            f"screen_by_1m_status IN ({_BENCHMARK_SQL})",
            name="ck_pediatric_audiology__screen_by_1m",
        ),
        CheckConstraint(
            f"diagnosis_by_3m_status IN ({_BENCHMARK_SQL})",
            name="ck_pediatric_audiology__diagnosis_by_3m",
        ),
        CheckConstraint(
            f"intervention_by_6m_status IN ({_BENCHMARK_SQL})",
            name="ck_pediatric_audiology__intervention_by_6m",
        ),
        CheckConstraint(
            f"ha_candidacy_confirmed_kind IS NULL OR ha_candidacy_confirmed_kind IN ({_CANDIDACY_SQL})",
            name="ck_pediatric_audiology__ha_candidacy_kind",
        ),
        CheckConstraint(
            f"ci_candidacy_confirmed_kind IS NULL OR ci_candidacy_confirmed_kind IN ({_CANDIDACY_SQL})",
            name="ck_pediatric_audiology__ci_candidacy_kind",
        ),
        Index(
            "uq_pediatric_audiology__live_patient",
            "live_patient_id",
            unique=True,
        ),
        Index(
            "ix_pediatric_audiology__clinic_id__patient_id",
            "clinic_id",
            "patient_id",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    screen_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    screen_result_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    screen_result_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rescreen_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rescreen_result_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rescreen_result_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    diagnostic_abr_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    diagnostic_abr_result_right: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    diagnostic_abr_result_left: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    permanent_hearing_loss: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    intervention_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    intervention_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    screen_by_1m_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    diagnosis_by_3m_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_applicable",
        server_default="not_applicable",
    )
    intervention_by_6m_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_applicable",
        server_default="not_applicable",
    )
    ehdi_engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    speech_language_milestones: Mapped[dict[str, Any] | list[Any] | None] = (
        mapped_column(JSON, nullable=True)
    )
    candidacy_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    ha_candidacy_confirmed_at: Mapped[datetime | None] = mapped_column(
        datetime6(), nullable=True
    )
    ha_candidacy_confirmed_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    ha_candidacy_confirmed_kind: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    ci_candidacy_confirmed_at: Mapped[datetime | None] = mapped_column(
        datetime6(), nullable=True
    )
    ci_candidacy_confirmed_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    ci_candidacy_confirmed_kind: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    live_patient_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        Computed(
            "CASE WHEN deleted_at IS NULL THEN patient_id ELSE NULL END",
            persisted=True,
        ),
    )

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    ha_candidacy_confirmed_by: Mapped[User | None] = relationship(
        foreign_keys=[ha_candidacy_confirmed_by_id], lazy="raise"
    )
    ci_candidacy_confirmed_by: Mapped[User | None] = relationship(
        foreign_keys=[ci_candidacy_confirmed_by_id], lazy="raise"
    )


class OmeEpisode(ClinicalRecordMixin, Base):
    __tablename__ = "ome_episode"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IN ({_LATERALITY_SQL})",
            name="ck_ome_episode__laterality",
        ),
        CheckConstraint(
            f"status IN ({_OME_STATUS_SQL})",
            name="ck_ome_episode__status",
        ),
        Index(
            "ix_ome_episode__clinic_id__patient_id__first_seen_on",
            "clinic_id",
            "patient_id",
            text("first_seen_on DESC"),
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    audiogram_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("audiogram.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    tympanometry_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("tympanometry.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    laterality: Mapped[str] = mapped_column(String(10), nullable=False)
    first_seen_on: Mapped[date] = mapped_column(Date, nullable=False)
    hearing_level_db: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    watchful_waiting_start_on: Mapped[date] = mapped_column(Date, nullable=False)
    watchful_waiting_due_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="watchful_waiting",
        server_default="watchful_waiting",
    )
    resolved_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id], lazy="raise"
    )
    audiogram: Mapped[Audiogram | None] = relationship(
        foreign_keys=[audiogram_id], lazy="raise"
    )
    tympanometry: Mapped[Tympanometry | None] = relationship(
        foreign_keys=[tympanometry_id], lazy="raise"
    )
