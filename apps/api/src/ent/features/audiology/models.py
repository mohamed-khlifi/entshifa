"""Audiogram ORM models (architecture §25.8 / P4-01)."""

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
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin, SurrogatePkMixin, TimestampMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint
from ent.core.db.types import ULIDType
from ent.features.audiology.constants import (
    ALL_FREQUENCIES_HZ,
    AUDIOGRAM_STATUSES,
    CONDUCTION_TYPES,
    EARS,
    PTA_FORMULAS,
    RELIABILITY_VALUES,
    TEST_METHODS,
    TRANSDUCERS,
)

if TYPE_CHECKING:
    from ent.features.encounters.models import Encounter
    from ent.features.patients.models import Patient
    from ent.features.users.models import User

_FREQ_SQL = ",".join(str(value) for value in ALL_FREQUENCIES_HZ)
_EAR_SQL = ",".join(f"'{value}'" for value in EARS)
_COND_SQL = ",".join(f"'{value}'" for value in CONDUCTION_TYPES)
_TRANSDUCER_SQL = ",".join(f"'{value}'" for value in TRANSDUCERS)
_METHOD_SQL = ",".join(f"'{value}'" for value in TEST_METHODS)
_RELIABILITY_SQL = ",".join(f"'{value}'" for value in RELIABILITY_VALUES)
_STATUS_SQL = ",".join(f"'{value}'" for value in AUDIOGRAM_STATUSES)
_PTA_SQL = ",".join(f"'{value}'" for value in PTA_FORMULAS)


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


def _in(column: str, values: str, *, nullable: bool) -> str:
    clause = f"{column} IN ({values})"
    if nullable:
        return f"{column} IS NULL OR {clause}"
    return clause


class Audiogram(ClinicalRecordMixin, Base):
    """Pure-tone audiogram header. Thresholds live in audiogram_threshold rows."""

    __tablename__ = "audiogram"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in("transducer", _TRANSDUCER_SQL, nullable=False),
            name="ck_audiogram__transducer",
        ),
        CheckConstraint(
            _in("method", _METHOD_SQL, nullable=False),
            name="ck_audiogram__method",
        ),
        CheckConstraint(
            _in("reliability", _RELIABILITY_SQL, nullable=False),
            name="ck_audiogram__reliability",
        ),
        CheckConstraint(
            _in("status", _STATUS_SQL, nullable=False),
            name="ck_audiogram__status",
        ),
        CheckConstraint(
            _in("pta_formula", _PTA_SQL, nullable=True),
            name="ck_audiogram__pta_formula",
        ),
        Index(
            "ix_audiogram__clinic_id__patient_id__performed_at",
            "clinic_id",
            "patient_id",
            text("performed_at DESC"),
        ),
        Index(
            "ix_audiogram__clinic_id__encounter_id",
            "clinic_id",
            "encounter_id",
        ),
        Index(
            "ix_audiogram__clinic_id__patient_id__is_baseline",
            "clinic_id",
            "patient_id",
            "is_baseline",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "patient.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_audiogram__patient",
        ),
        nullable=False,
    )
    encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_audiogram__encounter",
        ),
        nullable=True,
    )
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_audiogram__performed_by",
        ),
        nullable=False,
    )
    equipment: Mapped[str | None] = mapped_column(String(80), nullable=True)
    calibration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    transducer: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="headphones",
        server_default="headphones",
    )
    method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="standard",
        server_default="standard",
    )
    reliability: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="good",
        server_default="good",
    )
    is_baseline: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    pta_formula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pta_right: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    pta_left: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    abg_right: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    abg_left: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    grade_right: Mapped[str | None] = mapped_column(String(30), nullable=True)
    grade_left: Mapped[str | None] = mapped_column(String(30), nullable=True)
    loss_type_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    loss_type_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    configuration_right: Mapped[str | None] = mapped_column(String(30), nullable=True)
    configuration_left: Mapped[str | None] = mapped_column(String(30), nullable=True)
    asymmetry_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    shift_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    baseline_audiogram_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "audiogram.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_audiogram__baseline",
        ),
        nullable=True,
    )
    engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interpretation_text: Mapped[str | None] = mapped_column(
        _medium_text(), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id],
        lazy="raise",
    )
    performed_by: Mapped[User] = relationship(
        foreign_keys=[performed_by_id], lazy="raise"
    )
    baseline_audiogram: Mapped[Audiogram | None] = relationship(
        foreign_keys=[baseline_audiogram_id],
        lazy="raise",
    )
    metrics: Mapped[list[AudiologyMetric]] = relationship(
        back_populates="audiogram",
        primaryjoin=(
            "and_(Audiogram.id == AudiologyMetric.audiogram_id, "
            "AudiologyMetric.deleted_at.is_(None))"
        ),
        foreign_keys="AudiologyMetric.audiogram_id",
        lazy="selectin",
    )
    thresholds: Mapped[list[AudiogramThreshold]] = relationship(
        back_populates="audiogram",
        primaryjoin=(
            "and_(Audiogram.id == AudiogramThreshold.audiogram_id, "
            "AudiogramThreshold.deleted_at.is_(None))"
        ),
        foreign_keys="AudiogramThreshold.audiogram_id",
        lazy="selectin",
        order_by="AudiogramThreshold.ear, AudiogramThreshold.conduction, "
        "AudiogramThreshold.frequency_hz, AudiogramThreshold.is_masked",
    )


class AudiogramThreshold(ClinicalRecordMixin, Base):
    """One measured threshold point (never a JSON blob)."""

    __tablename__ = "audiogram_threshold"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"ear IN ({_EAR_SQL})",
            name="ck_audiogram_threshold__ear",
        ),
        CheckConstraint(
            f"conduction IN ({_COND_SQL})",
            name="ck_audiogram_threshold__conduction",
        ),
        CheckConstraint(
            f"frequency_hz IN ({_FREQ_SQL})",
            name="ck_audiogram_threshold__frequency_hz",
        ),
        CheckConstraint(
            "level_db IS NULL OR (level_db >= -10 AND level_db <= 130)",
            name="ck_audiogram_threshold__level_db",
        ),
        CheckConstraint(
            "(is_no_response = 0 AND level_db IS NOT NULL) OR is_no_response = 1",
            name="ck_audiogram_threshold__no_response_level",
        ),
        Index("ix_audiogram_threshold__audiogram_id", "audiogram_id"),
        Index(
            "ix_audiogram_threshold__audiogram_ear_cond",
            "audiogram_id",
            "ear",
            "conduction",
        ),
        Index(
            "ix_audiogram_threshold__clinic_audiogram",
            "clinic_id",
            "audiogram_id",
        ),
        Index(
            "uq_audiogram_threshold__point",
            "live_audiogram_id",
            "ear",
            "conduction",
            "frequency_hz",
            "is_masked",
            unique=True,
        ),
    )

    audiogram_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "audiogram.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_audiogram_threshold__audiogram",
        ),
        nullable=False,
    )
    ear: Mapped[str] = mapped_column(String(5), nullable=False)
    conduction: Mapped[str] = mapped_column(String(5), nullable=False)
    frequency_hz: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    level_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_masked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    is_no_response: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    live_audiogram_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        Computed(
            "CASE WHEN deleted_at IS NULL THEN audiogram_id ELSE NULL END",
            persisted=True,
        ),
    )

    audiogram: Mapped[Audiogram] = relationship(
        back_populates="thresholds",
        foreign_keys=[audiogram_id],
    )


class AudiologyMetric(ClinicalRecordMixin, Base):
    """Computed audiogram values kept for trending (architecture §25.8)."""

    __tablename__ = "audiology_metric"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            "ear IS NULL OR ear IN ('right','left')",
            name="ck_audiology_metric__ear",
        ),
        Index("ix_audiology_metric__audiogram_id", "audiogram_id"),
        Index(
            "uq_audiology_metric__audiogram_code_ear",
            "live_audiogram_id",
            "metric_code",
            "ear",
            unique=True,
        ),
    )

    audiogram_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "audiogram.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_audiology_metric__audiogram",
        ),
        nullable=False,
    )
    metric_code: Mapped[str] = mapped_column(String(40), nullable=False)
    ear: Mapped[str | None] = mapped_column(String(5), nullable=True)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    formula: Mapped[str] = mapped_column(String(80), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    live_audiogram_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        Computed(
            "CASE WHEN deleted_at IS NULL THEN audiogram_id ELSE NULL END",
            persisted=True,
        ),
    )

    audiogram: Mapped[Audiogram] = relationship(
        back_populates="metrics",
        foreign_keys=[audiogram_id],
    )


class AudiologyRequestIdempotency(SurrogatePkMixin, TimestampMixin, Base):
    """Idempotency-Key memory for audiogram creates."""

    __tablename__ = "audiology_request_idempotency"
    __table_args__ = (
        Index(
            "uq_audiology_idempotency__clinic_id__key",
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


from ent.features.audiology.guard import install_audiology_guards  # noqa: E402

install_audiology_guards(Audiogram, AudiogramThreshold)
