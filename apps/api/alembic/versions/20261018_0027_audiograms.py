"""Audiogram and audiogram_threshold tables (architecture §25.8 / P4-01).

Revision ID: 20261018_0027
Revises: 20261018_0026
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261018_0027"
down_revision: str | Sequence[str] | None = "20261018_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_FREQ = (
    "125,250,500,750,1000,1500,2000,3000,4000,6000,8000,"
    "10000,12500,14000,16000"
)
_TRANSDUCERS = "'headphones','inserts','free_field','bone_oscillator'"
_METHODS = "'standard','play','vra','boa','soundfield'"
_RELIABILITY = "'good','fair','poor'"
_STATUS = "'draft','final'"
_PTA = "'3freq','4freq_who','high_freq','fletcher'"


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
        "audiogram",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("equipment", sa.String(80), nullable=True),
        sa.Column("calibration_date", sa.Date(), nullable=True),
        sa.Column(
            "transducer",
            sa.String(30),
            nullable=False,
            server_default="headphones",
        ),
        sa.Column(
            "method",
            sa.String(30),
            nullable=False,
            server_default="standard",
        ),
        sa.Column(
            "reliability",
            sa.String(20),
            nullable=False,
            server_default="good",
        ),
        sa.Column(
            "is_baseline",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("pta_formula", sa.String(20), nullable=True),
        sa.Column("pta_right", sa.Numeric(5, 2), nullable=True),
        sa.Column("pta_left", sa.Numeric(5, 2), nullable=True),
        sa.Column("abg_right", sa.Numeric(5, 2), nullable=True),
        sa.Column("abg_left", sa.Numeric(5, 2), nullable=True),
        sa.Column("grade_right", sa.String(30), nullable=True),
        sa.Column("grade_left", sa.String(30), nullable=True),
        sa.Column("loss_type_right", sa.String(20), nullable=True),
        sa.Column("loss_type_left", sa.String(20), nullable=True),
        sa.Column("configuration_right", sa.String(30), nullable=True),
        sa.Column("configuration_left", sa.String(30), nullable=True),
        sa.Column(
            "asymmetry_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "shift_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("baseline_audiogram_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("engine_version", sa.String(20), nullable=True),
        sa.Column("interpretation_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_audiogram__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_audiogram__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_audiogram__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_audiogram__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_audiogram__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["baseline_audiogram_id"],
            ["audiogram.id"],
            name="fk_audiogram__baseline",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"transducer IN ({_TRANSDUCERS})",
            name="ck_audiogram__transducer",
        ),
        sa.CheckConstraint(
            f"method IN ({_METHODS})",
            name="ck_audiogram__method",
        ),
        sa.CheckConstraint(
            f"reliability IN ({_RELIABILITY})",
            name="ck_audiogram__reliability",
        ),
        sa.CheckConstraint(
            f"status IN ({_STATUS})",
            name="ck_audiogram__status",
        ),
        sa.CheckConstraint(
            f"pta_formula IS NULL OR pta_formula IN ({_PTA})",
            name="ck_audiogram__pta_formula",
        ),
    )
    op.create_index(
        "ix_audiogram__clinic_id__patient_id__performed_at",
        "audiogram",
        ["clinic_id", "patient_id", sa.text("performed_at DESC")],
    )
    op.create_index(
        "ix_audiogram__clinic_id__encounter_id",
        "audiogram",
        ["clinic_id", "encounter_id"],
    )
    op.create_index(
        "ix_audiogram__clinic_id__patient_id__is_baseline",
        "audiogram",
        ["clinic_id", "patient_id", "is_baseline"],
    )

    op.create_table(
        "audiogram_threshold",
        *_clinical_columns(),
        sa.Column("audiogram_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("ear", sa.String(5), nullable=False),
        sa.Column("conduction", sa.String(5), nullable=False),
        sa.Column("frequency_hz", sa.SmallInteger(), nullable=False),
        sa.Column("level_db", sa.SmallInteger(), nullable=True),
        sa.Column(
            "is_masked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_no_response",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "live_audiogram_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed(
                "CASE WHEN deleted_at IS NULL THEN audiogram_id ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_audiogram_threshold__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_audiogram_threshold__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["audiogram_id"],
            ["audiogram.id"],
            name="fk_audiogram_threshold__audiogram",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "ear IN ('right','left')",
            name="ck_audiogram_threshold__ear",
        ),
        sa.CheckConstraint(
            "conduction IN ('air','bone')",
            name="ck_audiogram_threshold__conduction",
        ),
        sa.CheckConstraint(
            f"frequency_hz IN ({_FREQ})",
            name="ck_audiogram_threshold__frequency_hz",
        ),
        sa.CheckConstraint(
            "level_db IS NULL OR (level_db >= -10 AND level_db <= 130)",
            name="ck_audiogram_threshold__level_db",
        ),
        sa.CheckConstraint(
            "(is_no_response = 0 AND level_db IS NOT NULL) OR is_no_response = 1",
            name="ck_audiogram_threshold__no_response_level",
        ),
        sa.UniqueConstraint(
            "live_audiogram_id",
            "ear",
            "conduction",
            "frequency_hz",
            "is_masked",
            name="uq_audiogram_threshold__point",
        ),
    )
    op.create_index(
        "ix_audiogram_threshold__audiogram_id",
        "audiogram_threshold",
        ["audiogram_id"],
    )
    op.create_index(
        "ix_audiogram_threshold__audiogram_ear_cond",
        "audiogram_threshold",
        ["audiogram_id", "ear", "conduction"],
    )
    op.create_index(
        "ix_audiogram_threshold__clinic_audiogram",
        "audiogram_threshold",
        ["clinic_id", "audiogram_id"],
    )

    op.create_table(
        "audiology_request_idempotency",
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
        sa.Column(
            "idempotency_key",
            sa.String(80, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column(
            "request_hash",
            sa.String(64, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_public_id", _ULID, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_audiology_idempotency__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_audiology_idempotency__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )
    op.create_index(
        "uq_audiology_idempotency__clinic_id__key",
        "audiology_request_idempotency",
        ["clinic_id", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    # InnoDB backs FK constraints with composite indexes; DROP INDEX fails with
    # 1553 while the constraint exists. DROP TABLE removes both.
    op.drop_table("audiology_request_idempotency")
    op.drop_table("audiogram_threshold")
    op.drop_table("audiogram")
