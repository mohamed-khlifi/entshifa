"""Create audit_log and access_log (architecture section 25.17 / P0-05)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0003"
down_revision: str | Sequence[str] | None = "20260320_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")


def _create_audit_like_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("request_id", _ULID, nullable=False),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("entity_public_id", _ULID, nullable=True),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("before_json", mysql.JSON(), nullable=True),
        sa.Column("after_json", mysql.JSON(), nullable=True),
        sa.Column("changed_fields", mysql.JSON(), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("ip_address", mysql.VARBINARY(16), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("occurred_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name=f"fk_{name}__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=f"fk_{name}__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=f"pk_{name}"),
        sa.UniqueConstraint("public_id", name=f"uq_{name}__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(f"ix_{name}__clinic_id__occurred_at", name, ["clinic_id", "occurred_at"])
    op.create_index(
        f"ix_{name}__clinic_id__user_id__occurred_at",
        name,
        ["clinic_id", "user_id", "occurred_at"],
    )
    op.create_index(f"ix_{name}__entity_type__entity_id", name, ["entity_type", "entity_id"])
    op.create_index(
        f"ix_{name}__clinic_id__patient_id__occurred_at",
        name,
        ["clinic_id", "patient_id", "occurred_at"],
    )


def upgrade() -> None:
    _create_audit_like_table("audit_log")
    _create_audit_like_table("access_log")


def downgrade() -> None:
    op.drop_table("access_log")
    op.drop_table("audit_log")
