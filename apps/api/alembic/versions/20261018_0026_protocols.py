"""Protocol and protocol_rule tables and recall foreign keys (P3-08).

Revision ID: 20261018_0026
Revises: 20261011_0025
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261018_0026"
down_revision: str | Sequence[str] | None = "20261011_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_TRIGGERS = "'procedure','diagnosis','finding','surgery','manual'"
_ACTIONS = "'visit','test','call','questionnaire','document'"


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


def upgrade() -> None:
    op.create_table(
        "protocol",
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
            sa.String(60, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("name_key", sa.String(80), nullable=False),
        sa.Column("trigger_type", sa.String(30), nullable=False),
        sa.Column("trigger_concept_ids", mysql.JSON(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.CheckConstraint(
            f"trigger_type IN ({_TRIGGERS})",
            name="ck_protocol__trigger_type",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_protocol__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_protocol"),
        sa.UniqueConstraint("public_id", name="uq_protocol__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_protocol__scope_clinic_id__code",
        "protocol",
        ["scope_clinic_id", "code"],
        unique=True,
    )
    op.create_index("ix_protocol__code", "protocol", ["code"])
    op.create_index(
        "ix_protocol__clinic_id__trigger_type",
        "protocol",
        ["clinic_id", "trigger_type"],
    )

    op.create_table(
        "protocol_rule",
        *_global_columns(),
        sa.Column("protocol_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("sequence", sa.SmallInteger(), nullable=False),
        sa.Column("offset_days", sa.Integer(), nullable=False),
        sa.Column("window_days", sa.SmallInteger(), nullable=False),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("action_config", mysql.JSON(), nullable=True),
        sa.Column("condition", mysql.JSON(), nullable=True),
        sa.Column("label_key", sa.String(80), nullable=False),
        sa.CheckConstraint("sequence >= 1", name="ck_protocol_rule__sequence"),
        sa.CheckConstraint("offset_days >= 0", name="ck_protocol_rule__offset_days"),
        sa.CheckConstraint(
            "window_days >= 0 AND window_days <= 180",
            name="ck_protocol_rule__window_days",
        ),
        sa.CheckConstraint(
            f"action_type IN ({_ACTIONS})",
            name="ck_protocol_rule__action_type",
        ),
        sa.ForeignKeyConstraint(
            ["protocol_id"],
            ["protocol.id"],
            name="fk_protocol_rule__protocol",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_protocol_rule"),
        sa.UniqueConstraint("public_id", name="uq_protocol_rule__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_protocol_rule__protocol_sequence",
        "protocol_rule",
        ["protocol_id", "sequence"],
        unique=True,
    )

    op.create_index(
        "ix_recall__clinic_id__protocol_rule_id",
        "recall",
        ["clinic_id", "protocol_rule_id"],
    )
    op.create_foreign_key(
        "fk_recall__protocol",
        "recall",
        "protocol",
        ["protocol_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_recall__protocol_rule",
        "recall",
        "protocol_rule",
        ["protocol_rule_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_recall__protocol_rule", "recall", type_="foreignkey")
    op.drop_constraint("fk_recall__protocol", "recall", type_="foreignkey")
    op.drop_index("ix_recall__clinic_id__protocol_rule_id", table_name="recall")
    op.drop_table("protocol_rule")
    op.drop_table("protocol")
