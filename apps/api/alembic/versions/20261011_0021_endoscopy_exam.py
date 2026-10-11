"""Create endoscopy_exam and attach procedure scores to observations (P3-02).

Revision ID: 20261011_0021
Revises: 20261011_0020
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261011_0021"
down_revision: str | Sequence[str] | None = "20261011_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_SCOPE = "'flexible','rigid_0','rigid_30','rigid_70'"
_SCALE = "'meltzer','lildholdt'"


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
        "endoscopy_exam",
        *_clinical_columns(),
        sa.Column("procedure_record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False),
        sa.Column(
            "decongestant_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "lund_kennedy_right",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "lund_kennedy_left",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "modified_lk_right",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "modified_lk_left",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("polyp_grade_right", sa.SmallInteger(), nullable=True),
        sa.Column("polyp_grade_left", sa.SmallInteger(), nullable=True),
        sa.Column("polyp_scale", sa.String(20), nullable=False),
        sa.Column("adenoid_obstruction_pct", sa.SmallInteger(), nullable=True),
        sa.Column("conclusion_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.CheckConstraint(
            f"scope_type IN ({_SCOPE})",
            name="ck_endoscopy_exam__scope_type",
        ),
        sa.CheckConstraint(
            f"polyp_scale IN ({_SCALE})",
            name="ck_endoscopy_exam__polyp_scale",
        ),
        sa.CheckConstraint(
            "lund_kennedy_right BETWEEN 0 AND 10",
            name="ck_endoscopy_exam__lk_right",
        ),
        sa.CheckConstraint(
            "lund_kennedy_left BETWEEN 0 AND 10",
            name="ck_endoscopy_exam__lk_left",
        ),
        sa.CheckConstraint(
            "modified_lk_right BETWEEN 0 AND 6",
            name="ck_endoscopy_exam__mod_right",
        ),
        sa.CheckConstraint(
            "modified_lk_left BETWEEN 0 AND 6",
            name="ck_endoscopy_exam__mod_left",
        ),
        sa.CheckConstraint(
            "polyp_grade_right IS NULL OR polyp_grade_right BETWEEN 0 AND 4",
            name="ck_endoscopy_exam__polyp_right",
        ),
        sa.CheckConstraint(
            "polyp_grade_left IS NULL OR polyp_grade_left BETWEEN 0 AND 4",
            name="ck_endoscopy_exam__polyp_left",
        ),
        sa.CheckConstraint(
            "adenoid_obstruction_pct IS NULL OR "
            "adenoid_obstruction_pct BETWEEN 0 AND 100",
            name="ck_endoscopy_exam__adenoid",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_endoscopy_exam__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_record_id"],
            ["procedure_record.id"],
            name="fk_endoscopy_exam__procedure",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_endoscopy_exam__public_id"),
        sa.UniqueConstraint(
            "procedure_record_id",
            name="uq_endoscopy_exam__procedure",
        ),
        sa.Index(
            "ix_endoscopy_exam__clinic_procedure",
            "clinic_id",
            "procedure_record_id",
        ),
    )
    op.add_column(
        "observation",
        sa.Column(
            "procedure_record_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_observation__clinic_procedure",
        "observation",
        ["clinic_id", "procedure_record_id"],
    )
    op.create_foreign_key(
        "fk_observation__procedure_record",
        "observation",
        "procedure_record",
        ["procedure_record_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.add_column(
        "calculation_result",
        sa.Column(
            "procedure_record_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_calc_result__clinic_procedure",
        "calculation_result",
        ["clinic_id", "procedure_record_id"],
    )
    op.create_foreign_key(
        "fk_calculation_result__procedure",
        "calculation_result",
        "procedure_record",
        ["procedure_record_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.execute(
        sa.text(
            "UPDATE setting "
            "SET value = JSON_QUOTE('meltzer') "
            "WHERE `key` = 'polyp_scale' "
            "AND JSON_UNQUOTE(value) = 'lund_kennedy'"
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_calculation_result__procedure",
        "calculation_result",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_calc_result__clinic_procedure",
        table_name="calculation_result",
    )
    op.drop_column("calculation_result", "procedure_record_id")
    op.drop_constraint(
        "fk_observation__procedure_record",
        "observation",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_observation__clinic_procedure",
        table_name="observation",
    )
    op.drop_column("observation", "procedure_record_id")
    op.drop_table("endoscopy_exam")
