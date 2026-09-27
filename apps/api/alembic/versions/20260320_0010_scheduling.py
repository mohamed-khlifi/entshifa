"""Scheduling tables (architecture §25.4 / P1-07).

Revision ID: 20260320_0010
Revises: 20260320_0009
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20260320_0010"
down_revision: str | Sequence[str] | None = "20260320_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS = "utf8mb4_0900_as_cs"
_STATUSES = "'scheduled','arrived','in_room','completed','no_show','cancelled'"


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
        "appointment_type",
        *_clinical_columns(),
        sa.Column("code", sa.String(40, collation=_CS), nullable=False),
        sa.Column("name_key", sa.String(80), nullable=False),
        sa.Column("default_duration_min", mysql.SMALLINT(), nullable=False),
        sa.Column("color", sa.String(12), nullable=False),
        sa.Column(
            "requires_room",
            mysql.TINYINT(display_width=1),
            nullable=False,
            server_default="0",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_appointment_type"),
        sa.UniqueConstraint("public_id", name="uq_appointment_type__public_id"),
        sa.UniqueConstraint(
            "clinic_id",
            "code",
            name="uq_appointment_type__clinic_id__code",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_appointment_type__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "default_duration_min > 0 AND default_duration_min <= 480",
            name="ck_appointment_type__duration",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "appointment",
        *_clinical_columns(),
        sa.Column("site_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("appointment_type_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("starts_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("ends_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason_text", sa.String(255), nullable=True),
        sa.Column("room", sa.String(40), nullable=True),
        sa.Column("created_from_recall_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("arrived_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("ended_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("cancellation_reason", sa.String(160), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_appointment"),
        sa.UniqueConstraint("public_id", name="uq_appointment__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_appointment__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["site.id"],
            name="fk_appointment__site",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_appointment__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_appointment__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_type_id"],
            ["appointment_type.id"],
            name="fk_appointment__appointment_type",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"status IN ({_STATUSES})",
            name="ck_appointment__status",
        ),
        sa.CheckConstraint("ends_at > starts_at", name="ck_appointment__time_range"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_appointment__clinic_id__user_id__starts_at",
        "appointment",
        ["clinic_id", "user_id", "starts_at"],
    )
    op.create_index(
        "ix_appointment__clinic_id__patient_id__starts_at",
        "appointment",
        ["clinic_id", "patient_id", "starts_at"],
    )
    op.create_index(
        "ix_appointment__clinic_id__status__starts_at",
        "appointment",
        ["clinic_id", "status", "starts_at"],
    )

    for table in ("appointment_type", "appointment"):
        op.create_foreign_key(
            f"fk_{table}__created_by",
            table,
            "user",
            ["created_by_id"],
            ["id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        )
        op.create_foreign_key(
            f"fk_{table}__updated_by",
            table,
            "user",
            ["updated_by_id"],
            ["id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        )
        op.create_foreign_key(
            f"fk_{table}__deleted_by",
            table,
            "user",
            ["deleted_by_id"],
            ["id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        )


def downgrade() -> None:
    # InnoDB uses a composite index whose leftmost column is the foreign-key
    # column as that constraint's index. DROP INDEX then raises 1553 while the
    # constraint still exists. DROP TABLE removes the constraint and indexes
    # together, so these indexes are not dropped on their own.
    op.drop_table("appointment")
    op.drop_table("appointment_type")
