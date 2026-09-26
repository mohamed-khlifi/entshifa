"""Create setting table and seed system clinical defaults (architecture §25.17 / P1-01).

Revision ID: 20260320_0007
Revises: 20260320_0006
Create Date: 2026-03-20 00:00:00

"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0007"
down_revision: str | Sequence[str] | None = "20260320_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS_80 = sa.String(80, collation="utf8mb4_0900_as_cs")

# Defaults from feature-spec §§8.5 / 7.x (tube recall). Written as data rows —
# not used as runtime Python fallbacks.
_SYSTEM_DEFAULTS: dict[str, object] = {
    # VERIFY: WHO 4-frequency is the common clinical default; clinics may switch.
    "pta_formula": "4freq_who",
    "asymmetry_rule": {
        "adjacent_db": 15,
        "adjacent_count": 2,
        "single_db": 20,
        "wrs_percent": 15,
    },
    # VERIFY: Meltzer 0–4 is the overall polyp grade option in the feature spec.
    "polyp_scale": "meltzer",
    "tube_recall_interval_months": 6,
    "follow_up_defaults": {
        "routine_months": 6,
        "post_op_days": 14,
    },
}


def _common_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
        sa.Column("public_id", _ULID, nullable=False),
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
        sa.Column(
            "version",
            mysql.INTEGER(unsigned=True),
            server_default=sa.text("1"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "setting",
        *_common_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("key", _CS_80, nullable=False),
        sa.Column("value", mysql.JSON(), nullable=False),
        # MySQL UNIQUE allows multiple NULLs; coalesce to 0 so system defaults
        # (clinic_id NULL, user_id NULL) remain unique per key.
        sa.Column(
            "scope_clinic_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("IFNULL(clinic_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "scope_user_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("IFNULL(user_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_setting__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_setting__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_setting"),
        sa.UniqueConstraint("public_id", name="uq_setting__public_id"),
        sa.UniqueConstraint(
            "scope_clinic_id",
            "scope_user_id",
            "key",
            name="uq_setting__clinic_id__user_id__key",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_setting__clinic_id", "setting", ["clinic_id"])
    op.create_index("ix_setting__user_id", "setting", ["user_id"])
    op.create_index("ix_setting__key", "setting", ["key"])

    now = datetime.now(UTC).replace(tzinfo=None)
    # Deterministic Crockford ULIDs for system rows (stable across environments).
    system_ulids = {
        "pta_formula": "01JP1A00000000000000000001",
        "asymmetry_rule": "01JP1A00000000000000000002",
        "polyp_scale": "01JP1A00000000000000000003",
        "tube_recall_interval_months": "01JP1A00000000000000000004",
        "follow_up_defaults": "01JP1A00000000000000000005",
    }
    bind = op.get_bind()
    for key, value in _SYSTEM_DEFAULTS.items():
        bind.execute(
            sa.text(
                "INSERT INTO setting "
                "(public_id, clinic_id, user_id, `key`, value, "
                "created_at, updated_at, version) "
                "VALUES (:public_id, NULL, NULL, :key, CAST(:value AS JSON), "
                ":created_at, :updated_at, 1)"
            ),
            {
                "public_id": system_ulids[key],
                "key": key,
                "value": json.dumps(value),
                "created_at": now,
                "updated_at": now,
            },
        )


def downgrade() -> None:
    op.drop_table("setting")
