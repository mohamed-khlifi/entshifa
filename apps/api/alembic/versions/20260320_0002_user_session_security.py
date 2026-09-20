"""Add session family, rotation, and active clinic to user_session (P0-04)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0002"
down_revision: str | Sequence[str] | None = "20260320_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS_64 = sa.String(64, collation="utf8mb4_0900_as_cs")


def upgrade() -> None:
    op.add_column(
        "user_session",
        sa.Column("session_family_id", _ULID, nullable=True),
    )
    op.add_column(
        "user_session",
        sa.Column("previous_refresh_token_hash", _CS_64, nullable=True),
    )
    op.add_column(
        "user_session",
        sa.Column("active_clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE user_session us
            JOIN `user` u ON u.id = us.user_id
            JOIN user_clinic_role ucr ON ucr.user_id = u.id
            SET us.session_family_id = us.public_id,
                us.active_clinic_id = ucr.clinic_id
            WHERE us.session_family_id IS NULL
            """
        )
    )

    op.alter_column(
        "user_session",
        "session_family_id",
        existing_type=_ULID,
        nullable=False,
    )
    op.alter_column(
        "user_session",
        "active_clinic_id",
        existing_type=mysql.BIGINT(unsigned=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_user_session__clinic",
        "user_session",
        "clinic",
        ["active_clinic_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_session__clinic", "user_session", type_="foreignkey")
    op.drop_column("user_session", "active_clinic_id")
    op.drop_column("user_session", "previous_refresh_token_hash")
    op.drop_column("user_session", "session_family_id")
