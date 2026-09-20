"""Create job_run (architecture section 25.17 / P0-07)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0004"
down_revision: str | Sequence[str] | None = "20260320_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")


def upgrade() -> None:
    op.create_table(
        "job_run",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("job_name", sa.String(80), nullable=False),
        sa.Column(
            "idempotency_key",
            sa.String(120, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("finished_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", mysql.JSON(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
        ),
        sa.CheckConstraint(
            "status IN ('pending','running','succeeded','failed','dead')",
            name="ck_job_run__status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_job_run"),
        sa.UniqueConstraint("public_id", name="uq_job_run__public_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_job_run__idempotency_key"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_job_run__status__started_at", "job_run", ["status", "started_at"])
    op.create_index(
        "ix_job_run__job_name__started_at",
        "job_run",
        ["job_name", "started_at"],
    )


def downgrade() -> None:
    op.drop_table("job_run")
