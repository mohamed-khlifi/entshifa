"""Hearing devices, pediatric audiology, OME tracking (P4-06 / architecture §25.8).

Revision ID: 20261019_0030
Revises: 20261018_0029
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261019_0030"
down_revision: str | Sequence[str] | None = "20261018_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_DEVICE_TYPES = (
    "'bte','ric','ite','cros','bone_conduction','cochlear_implant','middle_ear_implant'"
)
_DEVICE_STATUS = "'active','trial','inactive','replaced','removed'"
_SCREEN = "'pass','refer','not_tested'"
_ABR = "'normal','elevated','absent','not_tested'"
_INTERVENTION = (
    "'hearing_aid','cochlear_implant','speech_therapy','early_intervention','monitoring'"
)
_BENCHMARK = "'not_applicable','pending','met','late','overdue'"
_OME = "'watchful_waiting','resolved','persisted_tubes_proposed','tubes_inserted'"
_CANDIDACY = "'hearing_aid','cochlear_implant'"


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
    op.add_column(
        "audiogram",
        sa.Column(
            "is_minimum_response_level",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "audiogram",
        sa.Column(
            "is_binaural_soundfield",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_table(
        "hearing_device",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("ear", sa.String(5), nullable=False),
        sa.Column("device_type", sa.String(30), nullable=False),
        sa.Column("brand", sa.String(60), nullable=True),
        sa.Column("model", sa.String(60), nullable=True),
        sa.Column("serial", sa.String(60), nullable=True),
        sa.Column("fitted_on", sa.Date(), nullable=True),
        sa.Column("fitted_by", sa.String(120), nullable=True),
        sa.Column("warranty_end", sa.Date(), nullable=True),
        sa.Column("last_programmed_on", sa.Date(), nullable=True),
        sa.Column("battery_type", sa.String(40), nullable=True),
        sa.Column("daily_use_hours", sa.Numeric(4, 1), nullable=True),
        sa.Column("satisfaction", sa.SmallInteger(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("aided_thresholds", mysql.JSON(), nullable=True),
        sa.Column("surgeon", sa.String(120), nullable=True),
        sa.Column("surgery_date", sa.Date(), nullable=True),
        sa.Column("electrode_array", sa.String(80), nullable=True),
        sa.Column("implant_activation_date", sa.Date(), nullable=True),
        sa.Column("mapping_dates", mysql.JSON(), nullable=True),
        sa.Column("complications", sa.String(255), nullable=True),
        sa.Column("mri_conditions", sa.String(160), nullable=True),
        sa.Column("notes", mysql.MEDIUMTEXT(), nullable=True),
        sa.CheckConstraint("ear IN ('right','left')", name="ck_hearing_device__ear"),
        sa.CheckConstraint(
            f"device_type IN ({_DEVICE_TYPES})",
            name="ck_hearing_device__device_type",
        ),
        sa.CheckConstraint(
            f"status IN ({_DEVICE_STATUS})",
            name="ck_hearing_device__status",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_hearing_device__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_hearing_device__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_hearing_device__public_id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_hearing_device__clinic_id__patient_id__fitted_on",
        "hearing_device",
        ["clinic_id", "patient_id", sa.text("fitted_on DESC")],
    )
    op.create_index(
        "ix_hearing_device__clinic_id__status__warranty_end",
        "hearing_device",
        ["clinic_id", "status", "warranty_end"],
    )

    op.create_table(
        "pediatric_audiology_record",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("screen_date", sa.Date(), nullable=True),
        sa.Column("screen_result_right", sa.String(20), nullable=True),
        sa.Column("screen_result_left", sa.String(20), nullable=True),
        sa.Column("rescreen_date", sa.Date(), nullable=True),
        sa.Column("rescreen_result_right", sa.String(20), nullable=True),
        sa.Column("rescreen_result_left", sa.String(20), nullable=True),
        sa.Column("diagnostic_abr_date", sa.Date(), nullable=True),
        sa.Column("diagnostic_abr_result_right", sa.String(30), nullable=True),
        sa.Column("diagnostic_abr_result_left", sa.String(30), nullable=True),
        sa.Column(
            "permanent_hearing_loss",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("intervention_date", sa.Date(), nullable=True),
        sa.Column("intervention_type", sa.String(40), nullable=True),
        sa.Column(
            "screen_by_1m_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "diagnosis_by_3m_status",
            sa.String(20),
            nullable=False,
            server_default="not_applicable",
        ),
        sa.Column(
            "intervention_by_6m_status",
            sa.String(20),
            nullable=False,
            server_default="not_applicable",
        ),
        sa.Column("ehdi_engine_version", sa.String(20), nullable=True),
        sa.Column("speech_language_milestones", mysql.JSON(), nullable=True),
        sa.Column("candidacy_snapshot", mysql.JSON(), nullable=True),
        sa.Column("ha_candidacy_confirmed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("ha_candidacy_confirmed_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("ha_candidacy_confirmed_kind", sa.String(30), nullable=True),
        sa.Column("ci_candidacy_confirmed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("ci_candidacy_confirmed_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("ci_candidacy_confirmed_kind", sa.String(30), nullable=True),
        sa.Column(
            "live_patient_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed(
                "CASE WHEN deleted_at IS NULL THEN patient_id ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.CheckConstraint(
            f"screen_result_right IS NULL OR screen_result_right IN ({_SCREEN})",
            name="ck_pediatric_audiology__screen_r",
        ),
        sa.CheckConstraint(
            f"screen_by_1m_status IN ({_BENCHMARK})",
            name="ck_pediatric_audiology__screen_by_1m",
        ),
        sa.CheckConstraint(
            f"diagnosis_by_3m_status IN ({_BENCHMARK})",
            name="ck_pediatric_audiology__diagnosis_by_3m",
        ),
        sa.CheckConstraint(
            f"intervention_by_6m_status IN ({_BENCHMARK})",
            name="ck_pediatric_audiology__intervention_by_6m",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_pediatric_audiology__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_pediatric_audiology__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_pediatric_audiology__public_id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "uq_pediatric_audiology__live_patient",
        "pediatric_audiology_record",
        ["live_patient_id"],
        unique=True,
    )

    op.create_table(
        "ome_episode",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("audiogram_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("tympanometry_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("laterality", sa.String(10), nullable=False),
        sa.Column("first_seen_on", sa.Date(), nullable=False),
        sa.Column("hearing_level_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("watchful_waiting_start_on", sa.Date(), nullable=False),
        sa.Column("watchful_waiting_due_on", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="watchful_waiting",
        ),
        sa.Column("resolved_on", sa.Date(), nullable=True),
        sa.Column("notes", mysql.MEDIUMTEXT(), nullable=True),
        sa.CheckConstraint(
            "laterality IN ('right','left','bilateral')",
            name="ck_ome_episode__laterality",
        ),
        sa.CheckConstraint(
            f"status IN ({_OME})",
            name="ck_ome_episode__status",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_ome_episode__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_ome_episode__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["audiogram_id"],
            ["audiogram.id"],
            name="fk_ome_episode__audiogram",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tympanometry_id"],
            ["tympanometry.id"],
            name="fk_ome_episode__tympanometry",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_ome_episode__public_id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_ome_episode__clinic_id__patient_id__first_seen_on",
        "ome_episode",
        ["clinic_id", "patient_id", sa.text("first_seen_on DESC")],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ome_episode__clinic_id__patient_id__first_seen_on",
        table_name="ome_episode",
    )
    op.drop_table("ome_episode")
    op.drop_index(
        "uq_pediatric_audiology__live_patient",
        table_name="pediatric_audiology_record",
    )
    op.drop_table("pediatric_audiology_record")
    op.drop_index(
        "ix_hearing_device__clinic_id__status__warranty_end",
        table_name="hearing_device",
    )
    op.drop_index(
        "ix_hearing_device__clinic_id__patient_id__fitted_on",
        table_name="hearing_device",
    )
    op.drop_table("hearing_device")
    op.drop_column("audiogram", "is_binaural_soundfield")
    op.drop_column("audiogram", "is_minimum_response_level")
