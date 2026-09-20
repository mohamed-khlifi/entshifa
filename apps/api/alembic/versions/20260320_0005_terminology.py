"""Create terminology tables (architecture section 25.2 / P0-08)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0005"
down_revision: str | Sequence[str] | None = "20260320_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS = "utf8mb4_0900_as_cs"


def _ref_columns(*, include_version: bool = True) -> list[sa.Column[object]]:
    cols: list[sa.Column[object]] = [
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _ULID, nullable=False),
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
    ]
    if include_version:
        cols.append(
            sa.Column(
                "version",
                mysql.INTEGER(unsigned=True),
                nullable=False,
                server_default="1",
            ),
        )
    return cols


def upgrade() -> None:
    op.create_table(
        "code_system",
        *_ref_columns(include_version=False),
        sa.Column("code", sa.String(40, collation=_CS), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(40), nullable=True),
        sa.Column("uri", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_code_system"),
        sa.UniqueConstraint("public_id", name="uq_code_system__public_id"),
        sa.UniqueConstraint("code", name="uq_code_system__code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "concept",
        *_ref_columns(),
        sa.Column("code_system_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("code", sa.String(60, collation=_CS), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("parent_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("numeric_value", sa.Numeric(10, 3), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("properties", mysql.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.CheckConstraint(
            "kind IN ('finding','anatomy','diagnosis','procedure','qualifier',"
            "'laterality','unit','instrument_item','drug','allergy')",
            name="ck_concept__kind",
        ),
        sa.ForeignKeyConstraint(
            ["code_system_id"],
            ["code_system.id"],
            name="fk_concept__code_system",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["concept.id"],
            name="fk_concept__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_concept__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_concept"),
        sa.UniqueConstraint("public_id", name="uq_concept__public_id"),
        sa.UniqueConstraint("code_system_id", "code", name="uq_concept__code_system_id__code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_concept__kind__parent_id", "concept", ["kind", "parent_id"])
    op.create_index("ix_concept__clinic_id__kind", "concept", ["clinic_id", "kind"])
    op.create_index("ix_concept__clinic_id", "concept", ["clinic_id"])

    op.create_table(
        "concept_translation",
        *_ref_columns(),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("display", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(400), nullable=True),
        sa.Column("abbreviation", sa.String(40), nullable=True),
        sa.Column("patient_friendly", sa.String(400), nullable=True),
        sa.Column("synonyms", mysql.JSON(), nullable=True),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "clinic_scope",
            mysql.BIGINT(unsigned=True),
            sa.Computed("IFNULL(clinic_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_concept_translation__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_concept_translation__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_concept_translation"),
        sa.UniqueConstraint("public_id", name="uq_concept_translation__public_id"),
        sa.UniqueConstraint(
            "concept_id",
            "locale",
            "clinic_scope",
            name="uq_concept_translation__concept_id__locale__clinic_scope",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_concept_translation__locale", "concept_translation", ["locale"])
    op.execute(
        "CREATE FULLTEXT INDEX ft_concept_translation__display_full_name "
        "ON concept_translation (display, full_name)",
    )

    op.create_table(
        "concept_relationship",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("source_concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("target_concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.CheckConstraint(
            "type IN ('is_a','part_of','maps_to','site_of','default_normal_for')",
            name="ck_concept_relationship__type",
        ),
        sa.ForeignKeyConstraint(
            ["source_concept_id"],
            ["concept.id"],
            name="fk_concept_relationship__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_concept_id"],
            ["concept.id"],
            name="fk_concept_relationship__concept_target",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_concept_relationship"),
        sa.UniqueConstraint("public_id", name="uq_concept_relationship__public_id"),
        sa.UniqueConstraint(
            "source_concept_id",
            "target_concept_id",
            "type",
            name="uq_concept_relationship__source__target__type",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_concept_relationship__target_concept_id",
        "concept_relationship",
        ["target_concept_id"],
    )

    op.create_table(
        "value_set",
        *_ref_columns(),
        sa.Column("code", sa.String(60, collation=_CS), nullable=False),
        sa.Column("name_key", sa.String(80), nullable=False),
        sa.Column("description_key", sa.String(120), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_value_set"),
        sa.UniqueConstraint("public_id", name="uq_value_set__public_id"),
        sa.UniqueConstraint("code", name="uq_value_set__code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "value_set_member",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _ULID, nullable=False),
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
        sa.Column("deleted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("deleted_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("value_set_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "clinic_scope",
            mysql.BIGINT(unsigned=True),
            sa.Computed("IFNULL(clinic_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["value_set_id"],
            ["value_set.id"],
            name="fk_value_set_member__value_set",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concept.id"],
            name="fk_value_set_member__concept",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_value_set_member__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_value_set_member"),
        sa.UniqueConstraint("public_id", name="uq_value_set_member__public_id"),
        sa.UniqueConstraint(
            "value_set_id",
            "concept_id",
            "clinic_scope",
            name="uq_value_set_member__value_set_id__concept_id__clinic_scope",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_value_set_member__value_set_id__sort_order",
        "value_set_member",
        ["value_set_id", "sort_order"],
    )


def downgrade() -> None:
    op.drop_table("value_set_member")
    op.drop_table("value_set")
    op.drop_table("concept_relationship")
    op.execute("DROP INDEX ft_concept_translation__display_full_name ON concept_translation")
    op.drop_table("concept_translation")
    op.drop_table("concept")
    op.drop_table("code_system")
