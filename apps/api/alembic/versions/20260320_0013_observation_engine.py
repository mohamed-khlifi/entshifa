"""Create observation, observation_component, examination_snapshot (P2-01).

Revision ID: 20260320_0013
Revises: 20260320_0012
Create Date: 2026-03-20 00:00:00

``encounter_id`` has no foreign key until the encounter table exists (P2-02).
``encounter_public_id`` is the visit address until then.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0013"
down_revision: str | Sequence[str] | None = "20260320_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_VALUE_TYPES = "'code','numeric','boolean','text','range','ordinal'"
_LATERALITY = "'right','left','bilateral','midline','na'"


def _clinical_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
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
            server_default=sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
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


def _value_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("value_type", sa.String(20), nullable=False),
        sa.Column("value_concept_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("value_numeric", sa.Numeric(12, 4), nullable=True),
        sa.Column("value_unit", sa.String(20), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("value_text", sa.String(500), nullable=True),
        sa.Column("value_low", sa.Numeric(12, 4), nullable=True),
        sa.Column("value_high", sa.Numeric(12, 4), nullable=True),
        sa.Column("ordinal_value", sa.SmallInteger(), nullable=True),
        sa.Column("qualifiers", mysql.JSON(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "observation",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("encounter_public_id", _ULID, nullable=True),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("body_site_concept_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("map_region_code", sa.String(80), nullable=True),
        sa.Column("laterality", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *_value_columns(),
        sa.Column("effective_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("recorded_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("confirmed_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "derived_from_observation_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
        ),
        sa.Column("method_concept_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.CheckConstraint(
            f"laterality IN ({_LATERALITY})",
            name="ck_observation__laterality",
        ),
        sa.CheckConstraint(
            "status IN ('normal','abnormal','not_examined','unknown')",
            name="ck_observation__status",
        ),
        sa.CheckConstraint(
            f"value_type IN ({_VALUE_TYPES})",
            name="ck_observation__value_type",
        ),
        sa.CheckConstraint(
            "source IN ('clinician','technician','patient','device','ai_confirmed')",
            name="ck_observation__source",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_observation__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_observation__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_observation__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["body_site_concept_id"],
            ["concept.id"],
            name="fk_observation__body_site_concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["value_concept_id"],
            ["concept.id"],
            name="fk_observation__value_concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_id"],
            ["user.id"],
            name="fk_observation__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by_id"],
            ["user.id"],
            name="fk_observation__confirmed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["derived_from_observation_id"],
            ["observation.id"],
            name="fk_observation__derived_from",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["method_concept_id"],
            ["concept.id"],
            name="fk_observation__method_concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_observation"),
        sa.UniqueConstraint("public_id", name="uq_observation__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_observation__clinic_patient_concept_effective",
        "observation",
        ["clinic_id", "patient_id", "concept_id", sa.text("effective_at DESC")],
    )
    op.create_index(
        "ix_observation__clinic_encounter_body_site",
        "observation",
        ["clinic_id", "encounter_id", "body_site_concept_id"],
    )
    op.create_index(
        "ix_observation__clinic_encounter_public",
        "observation",
        ["clinic_id", "encounter_public_id"],
    )
    op.create_index(
        "ix_observation__clinic_concept_value_concept",
        "observation",
        ["clinic_id", "concept_id", "value_concept_id"],
    )
    op.create_index(
        "ix_observation__cohort_ordinal",
        "observation",
        ["clinic_id", "concept_id", "ordinal_value", "effective_at"],
    )

    op.create_table(
        "observation_component",
        *_clinical_columns(),
        sa.Column("observation_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        *_value_columns(),
        sa.CheckConstraint(
            f"value_type IN ({_VALUE_TYPES})",
            name="ck_observation_component__value_type",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_observation_component__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observation.id"],
            name="fk_observation_component__observation",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_observation_component__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["value_concept_id"],
            ["concept.id"],
            name="fk_observation_component__value_concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_observation_component"),
        sa.UniqueConstraint("public_id", name="uq_observation_component__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_observation_component__clinic_id__observation_id",
        "observation_component",
        ["clinic_id", "observation_id"],
    )

    op.create_table(
        "examination_snapshot",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("encounter_public_id", _ULID, nullable=True),
        sa.Column("map_id", sa.String(60), nullable=False),
        sa.Column("laterality", sa.String(10), nullable=True),
        sa.Column("payload", mysql.JSON(), nullable=False),
        sa.Column("rendered_svg_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY})",
            name="ck_examination_snapshot__laterality",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_examination_snapshot__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_examination_snapshot__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["rendered_svg_id"],
            ["attachment.id"],
            name="fk_examination_snapshot__attachment",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_examination_snapshot"),
        sa.UniqueConstraint("public_id", name="uq_examination_snapshot__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_examination_snapshot__clinic_patient_map_created",
        "examination_snapshot",
        ["clinic_id", "patient_id", "map_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_table("examination_snapshot")
    op.drop_table("observation_component")
    op.drop_table("observation")
