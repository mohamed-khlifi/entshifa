"""Create diagnosis and user_diagnosis_favorite (P2-07).

Revision ID: 20261004_0016
Revises: 20261004_0015
Create Date: 2026-10-04 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20261004_0016"
down_revision: str | Sequence[str] | None = "20261004_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
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


def upgrade() -> None:
    op.create_table(
        "diagnosis",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("laterality", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("certainty", sa.String(20), nullable=True),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column("note", sa.String(400), nullable=True),
        sa.Column("promoted_to_problem_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("recorded_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("effective_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column(
            "derived_from_diagnosis_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
        ),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            f"laterality IN ({_LATERALITY})",
            name="ck_diagnosis__laterality",
        ),
        sa.CheckConstraint(
            "status IN ('suspected','confirmed','ruled_out')",
            name="ck_diagnosis__status",
        ),
        sa.CheckConstraint(
            "source IN ('clinician','copy_forward')",
            name="ck_diagnosis__source",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_diagnosis__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_diagnosis__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_diagnosis__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_diagnosis__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["promoted_to_problem_id"],
            ["patient_problem.id"],
            name="fk_diagnosis__promoted_problem",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_id"],
            ["user.id"],
            name="fk_diagnosis__recorded_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["derived_from_diagnosis_id"],
            ["diagnosis.id"],
            name="fk_diagnosis__derived_from",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["user.id"],
            name="fk_diagnosis__created_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["user.id"],
            name="fk_diagnosis__updated_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_diagnosis__public_id"),
    )
    op.create_index(
        "ix_diagnosis__clinic_id__encounter_id",
        "diagnosis",
        ["clinic_id", "encounter_id"],
    )
    op.create_index(
        "ix_diagnosis__clinic_id__concept_id__created_at",
        "diagnosis",
        ["clinic_id", "concept_id", "created_at"],
    )
    op.create_index(
        "ix_diagnosis__clinic_id__patient_id__effective_at",
        "diagnosis",
        ["clinic_id", "patient_id", "effective_at"],
    )

    op.create_table(
        "user_diagnosis_favorite",
        *_clinical_columns(),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_user_dx_favorite__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_user_dx_favorite__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_user_dx_favorite__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["user.id"],
            name="fk_user_dx_favorite__created_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["user.id"],
            name="fk_user_dx_favorite__updated_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_user_dx_favorite__public_id"),
        sa.UniqueConstraint(
            "clinic_id",
            "user_id",
            "concept_id",
            name="uq_user_dx_favorite__clinic__user__concept",
        ),
    )
    op.create_index(
        "ix_user_dx_favorite__clinic_id__user_id__sort_order",
        "user_diagnosis_favorite",
        ["clinic_id", "user_id", "sort_order"],
    )


def downgrade() -> None:
    # InnoDB uses a composite index whose leftmost column is the foreign-key
    # column as that constraint's index. DROP INDEX then raises 1553 while the
    # constraint still exists. DROP TABLE removes the constraint and indexes
    # together, so these indexes are not dropped on their own.
    op.drop_table("user_diagnosis_favorite")
    op.drop_table("diagnosis")
