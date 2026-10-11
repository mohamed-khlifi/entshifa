"""Create recall, recall_action, and recall idempotency (P2-11).

Revision ID: 20261011_0019
Revises: 20261011_0018
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261011_0019"
down_revision: str | Sequence[str] | None = "20261011_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_STATUS = "'pending','booked','done','overdue','cancelled','unreachable'"
_ACTIONS = "'visit','test','call','questionnaire','document'"
_SOURCES = "'manual'"
_LATERALITY = "'right','left','bilateral','midline','na'"
_CONTACTS = "'sms','call','email','whatsapp','booked'"
_OUTCOMES = "'reached','no_answer','voicemail','unreachable','confirmed','declined'"


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
        "recall",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("protocol_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("protocol_rule_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("reason_key", sa.String(80), nullable=True),
        sa.Column("reason_text", sa.String(255), nullable=True),
        sa.Column("reason_locale", sa.String(10), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column(
            "window_days",
            sa.SmallInteger(),
            nullable=False,
            server_default="14",
        ),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("action_config", mysql.JSON(), nullable=True),
        sa.Column("laterality", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("appointment_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("completed_encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("cancelled_reason", sa.String(200), nullable=True),
        sa.Column("assigned_to_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.CheckConstraint(f"status IN ({_STATUS})", name="ck_recall__status"),
        sa.CheckConstraint(
            f"action_type IN ({_ACTIONS})", name="ck_recall__action_type"
        ),
        sa.CheckConstraint(
            f"source_type IN ({_SOURCES})", name="ck_recall__source_type"
        ),
        sa.CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY})",
            name="ck_recall__laterality",
        ),
        sa.CheckConstraint(
            "window_days >= 0 AND window_days <= 180",
            name="ck_recall__window_days",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_recall__attempts"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_recall__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_recall__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointment.id"],
            name="fk_recall__appointment",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["completed_encounter_id"],
            ["encounter.id"],
            name="fk_recall__completed_encounter",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_id"],
            ["user.id"],
            name="fk_recall__assigned_to",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_recall__public_id"),
    )
    op.create_index("ix_recall__clinic_id", "recall", ["clinic_id"])
    op.create_index(
        "ix_recall__clinic_id__status__due_on",
        "recall",
        ["clinic_id", "status", "due_on"],
    )
    op.create_index(
        "ix_recall__clinic_id__patient_id__status",
        "recall",
        ["clinic_id", "patient_id", "status"],
    )
    op.create_index(
        "ix_recall__clinic_id__patient_id__due_on",
        "recall",
        ["clinic_id", "patient_id", sa.text("due_on DESC")],
    )
    op.create_table(
        "recall_action",
        *_clinical_columns(),
        sa.Column("recall_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("performed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("performed_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("outcome", sa.String(40), nullable=True),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("note_locale", sa.String(10), nullable=True),
        sa.CheckConstraint(f"action IN ({_CONTACTS})", name="ck_recall_action__action"),
        sa.CheckConstraint(
            f"outcome IS NULL OR outcome IN ({_OUTCOMES})",
            name="ck_recall_action__outcome",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_recall_action__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recall_id"],
            ["recall.id"],
            name="fk_recall_action__recall",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["user.id"],
            name="fk_recall_action__performed_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_recall_action__public_id"),
    )
    op.create_index("ix_recall_action__clinic_id", "recall_action", ["clinic_id"])
    op.create_index(
        "ix_recall_action__clinic_id__recall_id__performed_at",
        "recall_action",
        ["clinic_id", "recall_id", "performed_at"],
    )
    op.create_table(
        "recall_request_idempotency",
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
        sa.Column(
            "idempotency_key",
            sa.String(80, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column(
            "request_hash",
            sa.String(64, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("resource_public_id", _ULID, nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_recall_request_idempotency__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "public_id", name="uq_recall_request_idempotency__public_id"
        ),
    )
    op.create_index(
        "uq_recall_idempotency__clinic_id__idempotency_key",
        "recall_request_idempotency",
        ["clinic_id", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    # InnoDB uses a composite index whose leftmost column is the foreign-key
    # column as that constraint's index. DROP INDEX then raises 1553 while the
    # constraint still exists. DROP TABLE removes the constraint and indexes
    # together.
    op.drop_table("recall_action")
    op.drop_table("recall")
    op.drop_table("recall_request_idempotency")
