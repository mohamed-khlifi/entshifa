"""Staff invitations and password-reset tokens (P1-02).

Revision ID: 20260320_0008
Revises: 20260320_0007
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0008"
down_revision: str | Sequence[str] | None = "20260320_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS_190 = sa.String(190, collation="utf8mb4_0900_as_cs")
_HASH = sa.String(64, collation="utf8mb4_0900_as_cs")


def _common_columns(*, with_clinic: bool) -> list[sa.Column[object]]:
    columns: list[sa.Column[object]] = [
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
        sa.Column("public_id", _ULID, nullable=False),
    ]
    if with_clinic:
        columns.append(
            sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        )
    columns.extend(
        [
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
    )
    return columns


def upgrade() -> None:
    op.create_table(
        "user_invitation",
        *_common_columns(with_clinic=True),
        sa.Column("email", _CS_190, nullable=False),
        sa.Column("role_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("site_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("token_hash", _HASH, nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("accepted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("invited_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_user_invitation__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role.id"],
            name="fk_user_invitation__role",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["site.id"],
            name="fk_user_invitation__site",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_id"],
            ["user.id"],
            name="fk_user_invitation__invited_by",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_invitation"),
        sa.UniqueConstraint("public_id", name="uq_user_invitation__public_id"),
        sa.UniqueConstraint("token_hash", name="uq_user_invitation__token_hash"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_user_invitation__clinic_id__email",
        "user_invitation",
        ["clinic_id", "email"],
    )

    op.create_table(
        "password_reset_token",
        *_common_columns(with_clinic=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("token_hash", _HASH, nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("used_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_password_reset_token__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_password_reset_token"),
        sa.UniqueConstraint("public_id", name="uq_password_reset_token__public_id"),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_token__token_hash"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_password_reset_token__user_id__expires_at",
        "password_reset_token",
        ["user_id", "expires_at"],
    )


def downgrade() -> None:
    op.drop_table("password_reset_token")
    op.drop_table("user_invitation")
