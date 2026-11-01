"""Speech, tympanometry, OAE and ABR tables (P4-03 / architecture §25.8).

Revision ID: 20261018_0029
Revises: 20261018_0028
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261018_0029"
down_revision: str | Sequence[str] | None = "20261018_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_EAR = "'right','left'"
_JERGER = "'A','As','Ad','B','C'"
_PROBE = "226,1000"
_ETF = "'intact','impaired','patulous','not_performed'"
_REFLEX_FREQ = "500,1000,2000,4000"
_REFLEX_MODE = "'ipsi','contra'"
_REFLEX_STATUS = "'present','absent','elevated','not_tested'"
_OAE_TYPE = "'teoae','dpoae'"
_OAE_RESULT = "'pass','refer','partial','not_testable'"
_OAE_STAGE = "'first','second','diagnostic'"
_ABR_STIM = "'click','tone_burst','assr'"
_ABR_MORPH = "'normal','poor','absent','reproducible'"


def _clinical_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
        sa.Column("created_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("updated_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("deleted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("deleted_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "version",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="1",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "speech_audiometry",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("audiogram_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("ear", sa.String(5), nullable=False),
        sa.Column("srt_db", sa.SmallInteger(), nullable=True),
        sa.Column("sdt_db", sa.SmallInteger(), nullable=True),
        sa.Column("wrs_percent", sa.SmallInteger(), nullable=True),
        sa.Column("wrs_level_db", sa.SmallInteger(), nullable=True),
        sa.Column("additional_wrs_points", mysql.JSON(), nullable=True),
        sa.Column("word_list", sa.String(60), nullable=True),
        sa.Column("list_locale", sa.String(10), nullable=True),
        sa.Column("mcl_db", sa.SmallInteger(), nullable=True),
        sa.Column("ucl_db", sa.SmallInteger(), nullable=True),
        sa.Column("rollover", sa.Boolean(), nullable=True),
        sa.Column("sin_test", sa.String(60), nullable=True),
        sa.Column("sin_snr_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("sin_score_percent", sa.SmallInteger(), nullable=True),
        sa.Column(
            "speech_pta_discrepancy_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_speech_audiometry__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_speech_audiometry__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_speech_audiometry__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_speech_audiometry__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["audiogram_id"],
            ["audiogram.id"],
            name="fk_speech_audiometry__audiogram",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_speech_audiometry__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(f"ear IN ({_EAR})", name="ck_speech_audiometry__ear"),
        sa.CheckConstraint(
            "srt_db IS NULL OR (srt_db >= -10 AND srt_db <= 130)",
            name="ck_speech_audiometry__srt_db",
        ),
        sa.CheckConstraint(
            "wrs_percent IS NULL OR (wrs_percent >= 0 AND wrs_percent <= 100)",
            name="ck_speech_audiometry__wrs_percent",
        ),
    )
    op.create_index(
        "ix_speech_audiometry__clinic_id__patient_id__performed_at",
        "speech_audiometry",
        ["clinic_id", "patient_id", sa.text("performed_at DESC")],
    )
    op.create_index(
        "ix_speech_audiometry__clinic_id__audiogram_id",
        "speech_audiometry",
        ["clinic_id", "audiogram_id"],
    )

    op.create_table(
        "tympanometry",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("ear", sa.String(5), nullable=False),
        sa.Column(
            "probe_tone_hz",
            sa.SmallInteger(),
            nullable=False,
            server_default="226",
        ),
        sa.Column("ecv_ml", sa.Numeric(5, 2), nullable=True),
        sa.Column("peak_pressure_dapa", sa.SmallInteger(), nullable=True),
        sa.Column("compliance_ml", sa.Numeric(5, 2), nullable=True),
        sa.Column("gradient_dapa", sa.SmallInteger(), nullable=True),
        sa.Column("suggested_jerger_type", sa.String(5), nullable=True),
        sa.Column("jerger_type", sa.String(5), nullable=True),
        sa.Column(
            "jerger_type_is_overridden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("overridden_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("overridden_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "large_canal_volume_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("etf_result", sa.String(30), nullable=True),
        sa.Column("engine_version", sa.String(20), nullable=True),
        sa.Column("interpretation_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_tympanometry__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_tympanometry__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_tympanometry__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_tympanometry__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_tympanometry__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["overridden_by_id"],
            ["user.id"],
            name="fk_tympanometry__overridden_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(f"ear IN ({_EAR})", name="ck_tympanometry__ear"),
        sa.CheckConstraint(
            f"probe_tone_hz IN ({_PROBE})",
            name="ck_tympanometry__probe_tone_hz",
        ),
        sa.CheckConstraint(
            f"suggested_jerger_type IS NULL OR suggested_jerger_type IN ({_JERGER})",
            name="ck_tympanometry__suggested_jerger_type",
        ),
        sa.CheckConstraint(
            f"jerger_type IS NULL OR jerger_type IN ({_JERGER})",
            name="ck_tympanometry__jerger_type",
        ),
        sa.CheckConstraint(
            f"etf_result IS NULL OR etf_result IN ({_ETF})",
            name="ck_tympanometry__etf_result",
        ),
    )
    op.create_index(
        "ix_tympanometry__clinic_id__patient_id__performed_at",
        "tympanometry",
        ["clinic_id", "patient_id", sa.text("performed_at DESC")],
    )
    op.create_index(
        "ix_tympanometry__clinic_id__encounter_id",
        "tympanometry",
        ["clinic_id", "encounter_id"],
    )

    op.create_table(
        "acoustic_reflex",
        *_clinical_columns(),
        sa.Column("tympanometry_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("stimulus_ear", sa.String(5), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("frequency_hz", sa.SmallInteger(), nullable=False),
        sa.Column("threshold_db", sa.SmallInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "live_tympanometry_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed(
                "CASE WHEN deleted_at IS NULL THEN tympanometry_id ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_acoustic_reflex__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_acoustic_reflex__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tympanometry_id"],
            ["tympanometry.id"],
            name="fk_acoustic_reflex__tympanometry",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"stimulus_ear IN ({_EAR})",
            name="ck_acoustic_reflex__stimulus_ear",
        ),
        sa.CheckConstraint(
            f"mode IN ({_REFLEX_MODE})",
            name="ck_acoustic_reflex__mode",
        ),
        sa.CheckConstraint(
            f"frequency_hz IN ({_REFLEX_FREQ})",
            name="ck_acoustic_reflex__frequency_hz",
        ),
        sa.CheckConstraint(
            f"status IN ({_REFLEX_STATUS})",
            name="ck_acoustic_reflex__status",
        ),
        sa.UniqueConstraint(
            "live_tympanometry_id",
            "stimulus_ear",
            "mode",
            "frequency_hz",
            name="uq_acoustic_reflex__point",
        ),
    )
    op.create_index(
        "ix_acoustic_reflex__tympanometry_id",
        "acoustic_reflex",
        ["tympanometry_id"],
    )

    op.create_table(
        "oae_result",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("ear", sa.String(5), nullable=False),
        sa.Column("oae_type", sa.String(10), nullable=False),
        sa.Column("overall_result", sa.String(20), nullable=False),
        sa.Column("screening_stage", sa.String(20), nullable=True),
        sa.Column("bands", mysql.JSON(), nullable=False),
        sa.Column("interpretation_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_oae_result__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_oae_result__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_oae_result__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_oae_result__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_oae_result__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(f"ear IN ({_EAR})", name="ck_oae_result__ear"),
        sa.CheckConstraint(
            f"oae_type IN ({_OAE_TYPE})",
            name="ck_oae_result__oae_type",
        ),
        sa.CheckConstraint(
            f"overall_result IN ({_OAE_RESULT})",
            name="ck_oae_result__overall_result",
        ),
        sa.CheckConstraint(
            f"screening_stage IS NULL OR screening_stage IN ({_OAE_STAGE})",
            name="ck_oae_result__screening_stage",
        ),
    )
    op.create_index(
        "ix_oae_result__clinic_id__patient_id__performed_at",
        "oae_result",
        ["clinic_id", "patient_id", sa.text("performed_at DESC")],
    )

    op.create_table(
        "abr_result",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("ear", sa.String(5), nullable=False),
        sa.Column("stimulus", sa.String(20), nullable=False),
        sa.Column("stimulus_frequency_hz", sa.SmallInteger(), nullable=True),
        sa.Column("threshold_db", sa.SmallInteger(), nullable=True),
        sa.Column("intensity_db", sa.SmallInteger(), nullable=True),
        sa.Column("wave_i_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column("wave_iii_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column("wave_v_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column("i_iii_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column("iii_v_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column("i_v_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column("interaural_v_diff_ms", sa.Numeric(4, 2), nullable=True),
        sa.Column(
            "interaural_v_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("assr_thresholds", mysql.JSON(), nullable=True),
        sa.Column("morphology", sa.String(40), nullable=True),
        sa.Column("engine_version", sa.String(20), nullable=True),
        sa.Column("interpretation_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_abr_result__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_abr_result__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_abr_result__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_abr_result__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_abr_result__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(f"ear IN ({_EAR})", name="ck_abr_result__ear"),
        sa.CheckConstraint(
            f"stimulus IN ({_ABR_STIM})",
            name="ck_abr_result__stimulus",
        ),
        sa.CheckConstraint(
            f"morphology IS NULL OR morphology IN ({_ABR_MORPH})",
            name="ck_abr_result__morphology",
        ),
    )
    op.create_index(
        "ix_abr_result__clinic_id__patient_id__performed_at",
        "abr_result",
        ["clinic_id", "patient_id", sa.text("performed_at DESC")],
    )

    now = datetime.now(UTC).replace(tzinfo=None)
    op.get_bind().execute(
        sa.text(
            "INSERT INTO setting "
            "(public_id, clinic_id, user_id, `key`, value, created_at, updated_at, version) "
            "VALUES (:public_id, NULL, NULL, :key, CAST(:value AS JSON), "
            ":created_at, :updated_at, 1)"
        ),
        {
            "public_id": "01JP1A00000000000000000008",
            "key": "abr_interaural_v_threshold_ms",
            "value": json.dumps({"threshold_ms": 0.3}),
            "created_at": now,
            "updated_at": now,
        },
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM setting WHERE public_id = '01JP1A00000000000000000008'")
    )
    op.drop_table("abr_result")
    op.drop_table("oae_result")
    op.drop_table("acoustic_reflex")
    op.drop_table("tympanometry")
    op.drop_table("speech_audiometry")
