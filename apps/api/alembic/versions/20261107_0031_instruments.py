"""Questionnaire instrument tables (P5-01 / architecture §25.10).

Revision ID: 20261107_0031
Revises: 20261019_0030
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261107_0031"
down_revision: str | Sequence[str] | None = "20261019_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CATEGORIES = (
    "'sinonasal','ear','vertigo','voice','reflux','swallowing',"
    "'sleep','qol','head_neck','airway','pediatrics','other'"
)
_RESPONDENTS = "'patient','clinician','parent'"
_SCORING = "'sum','weighted_sum','custom'"
_LOCALES = "'en','fr','ar'"


def _global_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
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


def _version_child_columns() -> list[sa.Column[object]]:
    return list(_global_columns())


def upgrade() -> None:
    op.create_table(
        "instrument",
        *_global_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_clinic_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(clinic_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(40, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("respondent", sa.String(20), nullable=False),
        sa.Column("scoring_type", sa.String(30), nullable=False),
        sa.Column("min_score", sa.SmallInteger(), nullable=False),
        sa.Column("max_score", sa.SmallInteger(), nullable=False),
        sa.Column("mcid", sa.Numeric(6, 2), nullable=True),
        sa.Column("license_note", sa.String(255), nullable=False),
        sa.Column("reference", sa.String(255), nullable=False),
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.CheckConstraint(
            f"category IN ({_CATEGORIES})",
            name="ck_instrument__category",
        ),
        sa.CheckConstraint(
            f"respondent IN ({_RESPONDENTS})",
            name="ck_instrument__respondent",
        ),
        sa.CheckConstraint(
            f"scoring_type IN ({_SCORING})",
            name="ck_instrument__scoring_type",
        ),
        sa.CheckConstraint(
            "max_score >= min_score",
            name="ck_instrument__score_range",
        ),
        sa.CheckConstraint(
            "mcid IS NULL OR mcid > 0",
            name="ck_instrument__mcid",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_instrument__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_instrument__public_id"),
        sa.UniqueConstraint(
            "scope_clinic_id",
            "code",
            name="uq_instrument__scope_clinic_id__code",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index("ix_instrument__code", "instrument", ["code"])
    op.create_index(
        "ix_instrument__clinic_id__category",
        "instrument",
        ["clinic_id", "category"],
    )

    op.create_table(
        "instrument_version",
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
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
            server_default=sa.text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
        sa.Column("created_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("updated_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("deleted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("deleted_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("instrument_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "version",
            sa.String(20, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("scoring_config", mysql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_instrument_version__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.id"],
            name="fk_instrument_version__instrument",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_instrument_version__public_id"),
        sa.UniqueConstraint(
            "instrument_id",
            "version",
            name="uq_instrument_version__instrument_id__version",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_instrument_version__instrument_id__is_current",
        "instrument_version",
        ["instrument_id", "is_current"],
    )

    op.create_table(
        "instrument_item",
        *_version_child_columns(),
        sa.Column("instrument_version_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column(
            "code",
            sa.String(40, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("subscale", sa.String(40), nullable=True),
        sa.Column(
            "is_reverse_scored",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "weight",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="1.00",
        ),
        sa.CheckConstraint("position >= 1", name="ck_instrument_item__position"),
        sa.CheckConstraint("weight > 0", name="ck_instrument_item__weight"),
        sa.ForeignKeyConstraint(
            ["instrument_version_id"],
            ["instrument_version.id"],
            name="fk_instrument_item__instrument_version",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_instrument_item__public_id"),
        sa.UniqueConstraint(
            "instrument_version_id",
            "position",
            name="uq_instrument_item__version__position",
        ),
        sa.UniqueConstraint(
            "instrument_version_id",
            "code",
            name="uq_instrument_item__version__code",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "instrument_option",
        *_version_child_columns(),
        sa.Column("instrument_version_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("item_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_item_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(item_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("position >= 1", name="ck_instrument_option__position"),
        sa.ForeignKeyConstraint(
            ["instrument_version_id"],
            ["instrument_version.id"],
            name="fk_instrument_option__instrument_version",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["instrument_item.id"],
            name="fk_instrument_option__instrument_item",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_instrument_option__public_id"),
        sa.UniqueConstraint(
            "instrument_version_id",
            "scope_item_id",
            "position",
            name="uq_instrument_option__version__scope_item__position",
        ),
        sa.UniqueConstraint(
            "instrument_version_id",
            "scope_item_id",
            "value",
            name="uq_instrument_option__version__scope_item__value",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "instrument_translation",
        *_version_child_columns(),
        sa.Column("instrument_version_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("item_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("option_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_item_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(item_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "scope_option_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(option_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.CheckConstraint(
            f"locale IN ({_LOCALES})",
            name="ck_instrument_translation__locale",
        ),
        sa.CheckConstraint(
            "NOT (item_id IS NOT NULL AND option_id IS NOT NULL)",
            name="ck_instrument_translation__target",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_version_id"],
            ["instrument_version.id"],
            name="fk_instrument_translation__instrument_version",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["instrument_item.id"],
            name="fk_instrument_translation__instrument_item",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["instrument_option.id"],
            name="fk_instrument_translation__instrument_option",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_instrument_translation__public_id"),
        sa.UniqueConstraint(
            "instrument_version_id",
            "scope_item_id",
            "scope_option_id",
            "locale",
            name="uq_instrument_translation__version__scopes__locale",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )


def downgrade() -> None:
    op.drop_table("instrument_translation")
    op.drop_table("instrument_option")
    op.drop_table("instrument_item")
    op.drop_table("instrument_version")
    op.drop_table("instrument")
