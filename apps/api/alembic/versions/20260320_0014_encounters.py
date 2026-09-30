"""Create encounter tables and link existing visit foreign keys (P2-02).

Revision ID: 20260320_0014
Revises: 20260320_0013
Create Date: 2026-03-20 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0014"
down_revision: str | Sequence[str] | None = "20260320_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_TYPES = (
    "'consultation','follow_up','procedure','post_op','result_review','teleconsultation'"
)
_STATUSES = "'draft','signed','amended','cancelled'"
_LATERALITY = "'right','left','bilateral','midline','na'"


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


def _global_columns() -> list[sa.Column[object]]:
    columns = _clinical_columns()
    return [column for column in columns if column.name != "clinic_id"]


def upgrade() -> None:
    op.create_table(
        "encounter_template",
        *_global_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_clinic_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(clinic_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_user_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(user_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column("code", sa.String(60, collation="utf8mb4_0900_as_cs"), nullable=False),
        sa.Column("name_key", sa.String(80), nullable=False),
        sa.Column("trigger_concept_ids", mysql.JSON(), nullable=False),
        sa.Column("config", mysql.JSON(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_encounter_template__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_encounter_template__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_encounter_template"),
        sa.UniqueConstraint("public_id", name="uq_encounter_template__public_id"),
        sa.UniqueConstraint(
            "scope_clinic_id",
            "scope_user_id",
            "code",
            name="uq_encounter_template__scope__code",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_encounter_template__code",
        "encounter_template",
        ["code"],
    )

    op.create_table(
        "encounter",
        *_clinical_columns(),
        sa.Column("site_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("appointment_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("encounter_type", sa.String(30), nullable=False),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("ended_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("template_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("chief_complaint_summary", sa.String(255), nullable=True),
        sa.Column("history_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column("assessment_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column("plan_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("signed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("signed_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("locked_hash", sa.CHAR(64), nullable=True),
        sa.Column("previous_encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.CheckConstraint(
            f"encounter_type IN ({_TYPES})",
            name="ck_encounter__encounter_type",
        ),
        sa.CheckConstraint(
            f"status IN ({_STATUSES})",
            name="ck_encounter__status",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_encounter__time_range",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_encounter__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["site.id"],
            name="fk_encounter__site",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_encounter__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_encounter__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointment.id"],
            name="fk_encounter__appointment",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["encounter_template.id"],
            name="fk_encounter__template",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["signed_by_id"],
            ["user.id"],
            name="fk_encounter__signed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["previous_encounter_id"],
            ["encounter.id"],
            name="fk_encounter__previous",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_encounter"),
        sa.UniqueConstraint("public_id", name="uq_encounter__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_encounter__clinic_patient_started",
        "encounter",
        ["clinic_id", "patient_id", sa.text("started_at DESC")],
    )
    op.create_index(
        "ix_encounter__clinic_user_status",
        "encounter",
        ["clinic_id", "user_id", "status"],
    )

    op.create_table(
        "encounter_complaint",
        *_clinical_columns(),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("laterality", sa.String(10), nullable=True),
        sa.Column("duration_text", sa.String(60), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY})",
            name="ck_encounter_complaint__laterality",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_encounter_complaint__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_encounter_complaint__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_encounter_complaint__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_encounter_complaint"),
        sa.UniqueConstraint("public_id", name="uq_encounter_complaint__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_encounter_complaint__clinic_encounter",
        "encounter_complaint",
        ["clinic_id", "encounter_id"],
    )

    op.create_table(
        "encounter_addendum",
        *_clinical_columns(),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("author_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("body", mysql.MEDIUMTEXT(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_encounter_addendum__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_encounter_addendum__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
            name="fk_encounter_addendum__author",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_encounter_addendum"),
        sa.UniqueConstraint("public_id", name="uq_encounter_addendum__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_encounter_addendum__clinic_encounter_created",
        "encounter_addendum",
        ["clinic_id", "encounter_id", sa.text("created_at DESC")],
    )

    op.create_table(
        "encounter_signature",
        *_clinical_columns(),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("signed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("ip_address", mysql.VARBINARY(16), nullable=True),
        sa.Column("content_hash", sa.CHAR(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_encounter_signature__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_encounter_signature__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_encounter_signature__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_encounter_signature"),
        sa.UniqueConstraint("public_id", name="uq_encounter_signature__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_encounter_signature__clinic_encounter",
        "encounter_signature",
        ["clinic_id", "encounter_id"],
    )

    op.create_foreign_key(
        "fk_observation__encounter",
        "observation",
        "encounter",
        ["encounter_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_examination_snapshot__encounter",
        "examination_snapshot",
        "encounter",
        ["encounter_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_attachment__encounter",
        "attachment",
        "encounter",
        ["encounter_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_document__encounter",
        "document",
        "encounter",
        ["encounter_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_patient_problem__first_encounter",
        "patient_problem",
        "encounter",
        ["first_encounter_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_patient_problem__last_encounter",
        "patient_problem",
        "encounter",
        ["last_encounter_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_patient_problem__last_encounter", "patient_problem", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_patient_problem__first_encounter", "patient_problem", type_="foreignkey"
    )
    op.drop_constraint("fk_document__encounter", "document", type_="foreignkey")
    op.drop_constraint(
        "fk_attachment__encounter", "attachment", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_examination_snapshot__encounter",
        "examination_snapshot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_observation__encounter", "observation", type_="foreignkey"
    )
    op.drop_table("encounter_signature")
    op.drop_table("encounter_addendum")
    op.drop_table("encounter_complaint")
    op.drop_table("encounter")
    op.drop_table("encounter_template")
