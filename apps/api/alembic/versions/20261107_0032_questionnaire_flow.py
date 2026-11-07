"""Questionnaire invitation, response, and answer tables (P5-03).

Revision ID: 20261107_0032
Revises: 20261107_0031
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261107_0032"
down_revision: str | Sequence[str] | None = "20261107_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CHANNELS = "'sms','whatsapp','email','tablet'"
_CONTEXTS = (
    "'pre_visit','waiting_room','post_op_3m','post_op_6m','post_op_12m','follow_up'"
)
_ENTERED_BY = "'patient','staff','clinician'"
_LOCALES = "'en','fr','ar'"


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


def _answer_columns() -> list[sa.Column[object]]:
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
    ]


def upgrade() -> None:
    op.create_table(
        "questionnaire_invitation",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("instrument_version_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "token_hash",
            sa.CHAR(64, collation="utf8mb4_0900_as_cs"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("sent_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("opened_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("completed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("context", sa.String(40), nullable=False),
        sa.Column("related_surgery_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("recipient_address", sa.String(190), nullable=True),
        sa.CheckConstraint(
            f"channel IN ({_CHANNELS})", name="ck_questionnaire_invitation__channel"
        ),
        sa.CheckConstraint(
            f"context IN ({_CONTEXTS})", name="ck_questionnaire_invitation__context"
        ),
        sa.CheckConstraint(
            f"locale IN ({_LOCALES})", name="ck_questionnaire_invitation__locale"
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_version_id"],
            ["instrument_version.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_questionnaire_invitation__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_questionnaire_invitation__token_hash",
        "questionnaire_invitation",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_questionnaire_invitation__clinic_patient_sent",
        "questionnaire_invitation",
        ["clinic_id", "patient_id", "sent_at"],
        unique=False,
    )

    op.create_table(
        "questionnaire_response",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("instrument_version_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("invitation_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("completed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("entered_by", sa.String(20), nullable=False),
        sa.Column("total_score", sa.Numeric(7, 2), nullable=False),
        sa.Column("subscale_scores", mysql.JSON(), nullable=False),
        sa.Column("severity_band", sa.String(40), nullable=True),
        sa.Column("change_from_previous", sa.Numeric(7, 2), nullable=True),
        sa.Column("mcid_reached", sa.Boolean(), nullable=True),
        sa.Column("previous_response_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.CheckConstraint(
            f"locale IN ({_LOCALES})", name="ck_questionnaire_response__locale"
        ),
        sa.CheckConstraint(
            f"entered_by IN ({_ENTERED_BY})",
            name="ck_questionnaire_response__entered_by",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_version_id"],
            ["instrument_version.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounter.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["invitation_id"],
            ["questionnaire_invitation.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["previous_response_id"],
            ["questionnaire_response.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_questionnaire_response__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_questionnaire_response__clinic_patient_version_completed",
        "questionnaire_response",
        ["clinic_id", "patient_id", "instrument_version_id", "completed_at"],
        unique=False,
    )
    op.create_index(
        "uq_questionnaire_response__invitation_id",
        "questionnaire_response",
        ["invitation_id"],
        unique=True,
    )

    op.create_table(
        "questionnaire_answer",
        *_answer_columns(),
        sa.Column(
            "questionnaire_response_id", mysql.BIGINT(unsigned=True), nullable=False
        ),
        sa.Column("instrument_item_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["questionnaire_response_id"],
            ["questionnaire_response.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_item_id"],
            ["instrument_item.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_questionnaire_answer__public_id"),
        sa.UniqueConstraint(
            "questionnaire_response_id",
            "instrument_item_id",
            name="uq_questionnaire_answer__response__item",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "questionnaire_request_idempotency",
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
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
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
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
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "public_id", name="uq_questionnaire_idempotency__public_id"
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_questionnaire_idempotency__clinic_id__key",
        "questionnaire_request_idempotency",
        ["clinic_id", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("questionnaire_request_idempotency")
    op.drop_table("questionnaire_answer")
    op.drop_index(
        "uq_questionnaire_response__invitation_id",
        table_name="questionnaire_response",
    )
    op.drop_index(
        "ix_questionnaire_response__clinic_patient_version_completed",
        table_name="questionnaire_response",
    )
    op.drop_table("questionnaire_response")
    op.drop_index(
        "ix_questionnaire_invitation__clinic_patient_sent",
        table_name="questionnaire_invitation",
    )
    op.drop_index(
        "uq_questionnaire_invitation__token_hash",
        table_name="questionnaire_invitation",
    )
    op.drop_table("questionnaire_invitation")
