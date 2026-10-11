"""Create procedure_record and procedure_record_addendum (P3-01).

Revision ID: 20261011_0020
Revises: 20261011_0019
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261011_0020"
down_revision: str | Sequence[str] | None = "20261011_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_STATUS = "'draft','signed','amended'"
_SETTING = "'office','ot'"
_ANESTHESIA = "'none','topical_spray','local_infiltration','general'"
_TOLERANCE = (
    "'well_tolerated','mild_discomfort','moderate_discomfort',"
    "'poorly_tolerated','aborted'"
)
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
        "procedure_record",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("procedure_concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "laterality",
            sa.String(10),
            nullable=False,
            server_default="na",
        ),
        sa.Column(
            "anesthesia",
            sa.String(30),
            nullable=False,
            server_default="none",
        ),
        sa.Column(
            "setting",
            sa.String(20),
            nullable=False,
            server_default="office",
        ),
        sa.Column("instrument", sa.String(100), nullable=True),
        sa.Column("indication_text", sa.String(400), nullable=True),
        sa.Column("tolerance", sa.String(40), nullable=True),
        sa.Column(
            "complication_concept_id", mysql.BIGINT(unsigned=True), nullable=True
        ),
        sa.Column("complication_note", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("signed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("signed_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("signed_role", sa.String(30), nullable=True),
        sa.Column("signed_ip", sa.VARBINARY(16), nullable=True),
        sa.Column("locked_hash", sa.String(64), nullable=True),
        sa.CheckConstraint(
            f"status IN ({_STATUS})", name="ck_procedure_record__status"
        ),
        sa.CheckConstraint(
            f"setting IN ({_SETTING})", name="ck_procedure_record__setting"
        ),
        sa.CheckConstraint(
            f"anesthesia IN ({_ANESTHESIA})",
            name="ck_procedure_record__anesthesia",
        ),
        sa.CheckConstraint(
            f"laterality IN ({_LATERALITY})",
            name="ck_procedure_record__laterality",
        ),
        sa.CheckConstraint(
            f"tolerance IS NULL OR tolerance IN ({_TOLERANCE})",
            name="ck_procedure_record__tolerance",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_procedure_record__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_procedure_record__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            name="fk_procedure_record__encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_concept_id"],
            ["concept.id"],
            name="fk_procedure_record__procedure_concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_procedure_record__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["complication_concept_id"],
            ["concept.id"],
            name="fk_procedure_record__complication_concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["signed_by_id"],
            ["user.id"],
            name="fk_procedure_record__signed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_procedure_record__public_id"),
    )
    op.create_index("ix_procedure_record__clinic_id", "procedure_record", ["clinic_id"])
    op.create_index(
        "ix_procedure_record__clinic_id__patient_id__performed_at",
        "procedure_record",
        ["clinic_id", "patient_id", sa.text("performed_at DESC")],
    )
    op.create_index(
        "ix_procedure_record__clinic_id__procedure_concept_id",
        "procedure_record",
        ["clinic_id", "procedure_concept_id"],
    )
    op.create_index(
        "ix_procedure_record__clinic_id__encounter_id",
        "procedure_record",
        ["clinic_id", "encounter_id"],
    )
    op.create_index(
        "ix_procedure_record__clinic_id__status",
        "procedure_record",
        ["clinic_id", "status"],
    )
    op.create_table(
        "procedure_record_addendum",
        *_clinical_columns(),
        sa.Column("procedure_record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("author_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("body", mysql.MEDIUMTEXT(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_procedure_record_addendum__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_record_id"],
            ["procedure_record.id"],
            name="fk_procedure_record_addendum__procedure_record",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
            name="fk_procedure_record_addendum__author",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "public_id", name="uq_procedure_record_addendum__public_id"
        ),
    )
    op.create_index(
        "ix_procedure_record_addendum__clinic_id",
        "procedure_record_addendum",
        ["clinic_id"],
    )
    op.create_index(
        "ix_proc_addendum__clinic_proc_created",
        "procedure_record_addendum",
        ["clinic_id", "procedure_record_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    # DROP TABLE removes foreign keys and indexes together. Dropping an index
    # that InnoDB is using for a foreign key raises 1553.
    op.drop_table("procedure_record_addendum")
    op.drop_table("procedure_record")
