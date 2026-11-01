"""Speech, tympanometry, OAE and ABR ORM models (P4-03 / architecture §25.8)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
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
    ABR_MORPHOLOGIES,
    ABR_STIMULI,
    ACOUSTIC_REFLEX_FREQUENCIES_HZ,
    ACOUSTIC_REFLEX_MODES,
    ACOUSTIC_REFLEX_STATUSES,
    EARS,
    ETF_RESULTS,
    JERGER_TYPES,
    OAE_OVERALL_RESULTS,
    OAE_SCREENING_STAGES,
    OAE_TYPES,
    PROBE_TONE_HZ,
)

if TYPE_CHECKING:
    from ent.features.audiology.models import Audiogram
    from ent.features.encounters.models import Encounter
    from ent.features.patients.models import Patient
    from ent.features.users.models import User

_EAR_SQL = ",".join(f"'{value}'" for value in EARS)
_JERGER_SQL = ",".join(f"'{value}'" for value in JERGER_TYPES)
_PROBE_SQL = ",".join(str(value) for value in PROBE_TONE_HZ)
_ETF_SQL = ",".join(f"'{value}'" for value in ETF_RESULTS)
_REFLEX_FREQ_SQL = ",".join(str(value) for value in ACOUSTIC_REFLEX_FREQUENCIES_HZ)
_REFLEX_MODE_SQL = ",".join(f"'{value}'" for value in ACOUSTIC_REFLEX_MODES)
_REFLEX_STATUS_SQL = ",".join(f"'{value}'" for value in ACOUSTIC_REFLEX_STATUSES)
_OAE_TYPE_SQL = ",".join(f"'{value}'" for value in OAE_TYPES)
_OAE_RESULT_SQL = ",".join(f"'{value}'" for value in OAE_OVERALL_RESULTS)
_OAE_STAGE_SQL = ",".join(f"'{value}'" for value in OAE_SCREENING_STAGES)
_ABR_STIM_SQL = ",".join(f"'{value}'" for value in ABR_STIMULI)
_ABR_MORPH_SQL = ",".join(f"'{value}'" for value in ABR_MORPHOLOGIES)


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


class SpeechAudiometry(ClinicalRecordMixin, Base):
    __tablename__ = "speech_audiometry"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(f"ear IN ({_EAR_SQL})", name="ck_speech_audiometry__ear"),
        CheckConstraint(
            "srt_db IS NULL OR (srt_db >= -10 AND srt_db <= 130)",
            name="ck_speech_audiometry__srt_db",
        ),
        CheckConstraint(
            "sdt_db IS NULL OR (sdt_db >= -10 AND sdt_db <= 130)",
            name="ck_speech_audiometry__sdt_db",
        ),
        CheckConstraint(
            "wrs_percent IS NULL OR (wrs_percent >= 0 AND wrs_percent <= 100)",
            name="ck_speech_audiometry__wrs_percent",
        ),
        CheckConstraint(
            "wrs_level_db IS NULL OR (wrs_level_db >= -10 AND wrs_level_db <= 130)",
            name="ck_speech_audiometry__wrs_level_db",
        ),
        CheckConstraint(
            "mcl_db IS NULL OR (mcl_db >= -10 AND mcl_db <= 130)",
            name="ck_speech_audiometry__mcl_db",
        ),
        CheckConstraint(
            "ucl_db IS NULL OR (ucl_db >= -10 AND ucl_db <= 130)",
            name="ck_speech_audiometry__ucl_db",
        ),
        CheckConstraint(
            "sin_score_percent IS NULL OR (sin_score_percent >= 0 AND sin_score_percent <= 100)",
            name="ck_speech_audiometry__sin_score_percent",
        ),
        Index(
            "ix_speech_audiometry__clinic_id__patient_id__performed_at",
            "clinic_id",
            "patient_id",
            text("performed_at DESC"),
        ),
        Index(
            "ix_speech_audiometry__clinic_id__audiogram_id",
            "clinic_id",
            "audiogram_id",
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
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    ear: Mapped[str] = mapped_column(String(5), nullable=False)
    srt_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sdt_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    wrs_percent: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    wrs_level_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    additional_wrs_points: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSON, nullable=True
    )
    word_list: Mapped[str | None] = mapped_column(String(60), nullable=True)
    list_locale: Mapped[str | None] = mapped_column(String(10), nullable=True)
    mcl_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ucl_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    rollover: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sin_test: Mapped[str | None] = mapped_column(String(60), nullable=True)
    sin_snr_db: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    sin_score_percent: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    speech_pta_discrepancy_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id], lazy="raise"
    )
    audiogram: Mapped[Audiogram | None] = relationship(
        foreign_keys=[audiogram_id], lazy="raise"
    )
    performed_by: Mapped[User] = relationship(
        foreign_keys=[performed_by_id], lazy="raise"
    )


class Tympanometry(ClinicalRecordMixin, Base):
    __tablename__ = "tympanometry"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(f"ear IN ({_EAR_SQL})", name="ck_tympanometry__ear"),
        CheckConstraint(
            f"probe_tone_hz IN ({_PROBE_SQL})",
            name="ck_tympanometry__probe_tone_hz",
        ),
        CheckConstraint(
            "ecv_ml IS NULL OR (ecv_ml >= 0 AND ecv_ml <= 10)",
            name="ck_tympanometry__ecv_ml",
        ),
        CheckConstraint(
            "peak_pressure_dapa IS NULL OR (peak_pressure_dapa >= -600 AND peak_pressure_dapa <= 400)",
            name="ck_tympanometry__peak_pressure_dapa",
        ),
        CheckConstraint(
            "compliance_ml IS NULL OR (compliance_ml >= 0 AND compliance_ml <= 10)",
            name="ck_tympanometry__compliance_ml",
        ),
        CheckConstraint(
            "gradient_dapa IS NULL OR (gradient_dapa >= 0 AND gradient_dapa <= 600)",
            name="ck_tympanometry__gradient_dapa",
        ),
        CheckConstraint(
            f"suggested_jerger_type IS NULL OR suggested_jerger_type IN ({_JERGER_SQL})",
            name="ck_tympanometry__suggested_jerger_type",
        ),
        CheckConstraint(
            f"jerger_type IS NULL OR jerger_type IN ({_JERGER_SQL})",
            name="ck_tympanometry__jerger_type",
        ),
        CheckConstraint(
            f"etf_result IS NULL OR etf_result IN ({_ETF_SQL})",
            name="ck_tympanometry__etf_result",
        ),
        Index(
            "ix_tympanometry__clinic_id__patient_id__performed_at",
            "clinic_id",
            "patient_id",
            text("performed_at DESC"),
        ),
        Index(
            "ix_tympanometry__clinic_id__encounter_id",
            "clinic_id",
            "encounter_id",
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
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    ear: Mapped[str] = mapped_column(String(5), nullable=False)
    probe_tone_hz: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=226,
        server_default="226",
    )
    ecv_ml: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    peak_pressure_dapa: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    compliance_ml: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    gradient_dapa: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    suggested_jerger_type: Mapped[str | None] = mapped_column(String(5), nullable=True)
    jerger_type: Mapped[str | None] = mapped_column(String(5), nullable=True)
    jerger_type_is_overridden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    overridden_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    overridden_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    large_canal_volume_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    etf_result: Mapped[str | None] = mapped_column(String(30), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interpretation_text: Mapped[str | None] = mapped_column(
        _medium_text(), nullable=True
    )

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id], lazy="raise"
    )
    performed_by: Mapped[User] = relationship(
        foreign_keys=[performed_by_id], lazy="raise"
    )
    overridden_by: Mapped[User | None] = relationship(
        foreign_keys=[overridden_by_id], lazy="raise"
    )
    reflexes: Mapped[list[AcousticReflex]] = relationship(
        back_populates="tympanometry",
        primaryjoin=(
            "and_(Tympanometry.id == AcousticReflex.tympanometry_id, "
            "AcousticReflex.deleted_at.is_(None))"
        ),
        foreign_keys="AcousticReflex.tympanometry_id",
        lazy="selectin",
    )


class AcousticReflex(ClinicalRecordMixin, Base):
    __tablename__ = "acoustic_reflex"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"stimulus_ear IN ({_EAR_SQL})",
            name="ck_acoustic_reflex__stimulus_ear",
        ),
        CheckConstraint(
            f"mode IN ({_REFLEX_MODE_SQL})",
            name="ck_acoustic_reflex__mode",
        ),
        CheckConstraint(
            f"frequency_hz IN ({_REFLEX_FREQ_SQL})",
            name="ck_acoustic_reflex__frequency_hz",
        ),
        CheckConstraint(
            "threshold_db IS NULL OR (threshold_db >= 40 AND threshold_db <= 130)",
            name="ck_acoustic_reflex__threshold_db",
        ),
        CheckConstraint(
            f"status IN ({_REFLEX_STATUS_SQL})",
            name="ck_acoustic_reflex__status",
        ),
        Index("ix_acoustic_reflex__tympanometry_id", "tympanometry_id"),
        Index(
            "uq_acoustic_reflex__point",
            "live_tympanometry_id",
            "stimulus_ear",
            "mode",
            "frequency_hz",
            unique=True,
        ),
    )

    tympanometry_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("tympanometry.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    stimulus_ear: Mapped[str] = mapped_column(String(5), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    frequency_hz: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    threshold_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    live_tympanometry_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        Computed(
            "CASE WHEN deleted_at IS NULL THEN tympanometry_id ELSE NULL END",
            persisted=True,
        ),
    )

    tympanometry: Mapped[Tympanometry] = relationship(
        back_populates="reflexes",
        foreign_keys=[tympanometry_id],
    )


class OaeResult(ClinicalRecordMixin, Base):
    __tablename__ = "oae_result"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(f"ear IN ({_EAR_SQL})", name="ck_oae_result__ear"),
        CheckConstraint(
            f"oae_type IN ({_OAE_TYPE_SQL})",
            name="ck_oae_result__oae_type",
        ),
        CheckConstraint(
            f"overall_result IN ({_OAE_RESULT_SQL})",
            name="ck_oae_result__overall_result",
        ),
        CheckConstraint(
            f"screening_stage IS NULL OR screening_stage IN ({_OAE_STAGE_SQL})",
            name="ck_oae_result__screening_stage",
        ),
        Index(
            "ix_oae_result__clinic_id__patient_id__performed_at",
            "clinic_id",
            "patient_id",
            text("performed_at DESC"),
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
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    ear: Mapped[str] = mapped_column(String(5), nullable=False)
    oae_type: Mapped[str] = mapped_column(String(10), nullable=False)
    overall_result: Mapped[str] = mapped_column(String(20), nullable=False)
    screening_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bands: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    interpretation_text: Mapped[str | None] = mapped_column(
        _medium_text(), nullable=True
    )

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id], lazy="raise"
    )
    performed_by: Mapped[User] = relationship(
        foreign_keys=[performed_by_id], lazy="raise"
    )


class AbrResult(ClinicalRecordMixin, Base):
    __tablename__ = "abr_result"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(f"ear IN ({_EAR_SQL})", name="ck_abr_result__ear"),
        CheckConstraint(
            f"stimulus IN ({_ABR_STIM_SQL})",
            name="ck_abr_result__stimulus",
        ),
        CheckConstraint(
            "threshold_db IS NULL OR (threshold_db >= -10 AND threshold_db <= 130)",
            name="ck_abr_result__threshold_db",
        ),
        CheckConstraint(
            "intensity_db IS NULL OR (intensity_db >= 0 AND intensity_db <= 130)",
            name="ck_abr_result__intensity_db",
        ),
        CheckConstraint(
            f"morphology IS NULL OR morphology IN ({_ABR_MORPH_SQL})",
            name="ck_abr_result__morphology",
        ),
        Index(
            "ix_abr_result__clinic_id__patient_id__performed_at",
            "clinic_id",
            "patient_id",
            text("performed_at DESC"),
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
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    ear: Mapped[str] = mapped_column(String(5), nullable=False)
    stimulus: Mapped[str] = mapped_column(String(20), nullable=False)
    stimulus_frequency_hz: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    threshold_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    intensity_db: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    wave_i_ms: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    wave_iii_ms: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    wave_v_ms: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    i_iii_ms: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    iii_v_ms: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    i_v_ms: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    interaural_v_diff_ms: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    interaural_v_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    assr_thresholds: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    morphology: Mapped[str | None] = mapped_column(String(40), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interpretation_text: Mapped[str | None] = mapped_column(
        _medium_text(), nullable=True
    )

    patient: Mapped[Patient] = relationship(foreign_keys=[patient_id], lazy="raise")
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id], lazy="raise"
    )
    performed_by: Mapped[User] = relationship(
        foreign_keys=[performed_by_id], lazy="raise"
    )
