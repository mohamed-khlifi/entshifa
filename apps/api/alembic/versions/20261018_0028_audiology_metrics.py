"""Audiology metric table and shift_rule setting (P4-02).

Revision ID: 20261018_0028
Revises: 20261018_0027
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261018_0028"
down_revision: str | Sequence[str] | None = "20261018_0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")


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
        "audiology_metric",
        *_clinical_columns(),
        sa.Column("audiogram_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("metric_code", sa.String(40), nullable=False),
        sa.Column("ear", sa.String(5), nullable=True),
        sa.Column("value", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("formula", sa.String(80), nullable=False),
        sa.Column("engine_version", sa.String(20), nullable=False),
        sa.Column("computed_at", mysql.DATETIME(fsp=6), nullable=False),
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
        sa.UniqueConstraint("public_id", name="uq_audiology_metric__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_audiology_metric__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["audiogram_id"],
            ["audiogram.id"],
            name="fk_audiology_metric__audiogram",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "ear IS NULL OR ear IN ('right','left')",
            name="ck_audiology_metric__ear",
        ),
        sa.UniqueConstraint(
            "live_audiogram_id",
            "metric_code",
            "ear",
            name="uq_audiology_metric__audiogram_code_ear",
        ),
    )
    op.create_index(
        "ix_audiology_metric__audiogram_id",
        "audiology_metric",
        ["audiogram_id"],
    )

    now = datetime.now(UTC).replace(tzinfo=None)
    op.get_bind().execute(
        sa.text(
            "INSERT INTO setting "
            "(public_id, clinic_id, user_id, `key`, value, created_at, updated_at, version) "
            "VALUES (:public_id, NULL, NULL, :key, CAST(:value AS JSON), "
            ":created_at, :updated_at, 1)"
        ),
        {
            "public_id": "01JP1A00000000000000000007",
            "key": "shift_rule",
            "value": json.dumps({"rule": "asha"}),
            "created_at": now,
            "updated_at": now,
        },
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM setting WHERE public_id = '01JP1A00000000000000000007'")
    )
    op.drop_table("audiology_metric")
