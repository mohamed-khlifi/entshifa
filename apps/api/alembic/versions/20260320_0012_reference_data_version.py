"""Create reference_data_version (architecture §25.17 / §28, P1-11).

Revision ID: 20260320_0012
Revises: 20260320_0011
Create Date: 2026-03-20 00:00:00

``version`` is the dataset label, not the section 23 optimistic-lock counter.
Rows are insert-only. Datasets are the architecture examples plus the Phase 1
seed datasets ``permissions`` and ``templates``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0012"
down_revision: str | Sequence[str] | None = "20260320_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CS = "utf8mb4_0900_as_cs"


def upgrade() -> None:
    op.create_table(
        "reference_data_version",
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
        sa.Column("public_id", sa.CHAR(26, collation=_CS), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
            nullable=False,
        ),
        sa.Column("created_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("updated_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("deleted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("deleted_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("dataset", sa.String(60, collation=_CS), nullable=False),
        sa.Column("version", sa.String(40, collation=_CS), nullable=False),
        sa.Column("applied_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("applied_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("notes", mysql.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["applied_by_id"],
            ["user.id"],
            name="fk_reference_data_version__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reference_data_version"),
        sa.UniqueConstraint("public_id", name="uq_reference_data_version__public_id"),
        sa.UniqueConstraint(
            "dataset",
            "version",
            name="uq_reference_data_version__dataset__version",
        ),
        sa.CheckConstraint(
            "dataset IN ('formulary','instruments','protocols',"
            "'terminology','permissions','templates')",
            name="ck_reference_data_version__dataset",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_reference_data_version__dataset",
        "reference_data_version",
        ["dataset"],
    )
    op.create_index(
        "ix_reference_data_version__applied_by_id",
        "reference_data_version",
        ["applied_by_id"],
    )


def downgrade() -> None:
    op.drop_table("reference_data_version")
