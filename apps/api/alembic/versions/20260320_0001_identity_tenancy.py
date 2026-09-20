"""Identity and tenancy tables (architecture section 25.1).

Revision ID: 20260320_0001
Revises:
Create Date: 2026-03-20 00:00:00

Creates: clinic, site, user, role, permission, role_permission,
user_clinic_role, user_session.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS_80 = sa.String(80, collation="utf8mb4_0900_as_cs")
_CS_40 = sa.String(40, collation="utf8mb4_0900_as_cs")
_CS_190 = sa.String(190, collation="utf8mb4_0900_as_cs")
_CS_64 = sa.String(64, collation="utf8mb4_0900_as_cs")


def _common_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
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
        "clinic",
        *_common_columns(),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("legal_name", sa.String(160), nullable=True),
        sa.Column("slug", _CS_80, nullable=False),
        sa.Column("default_locale", sa.String(10), nullable=False),
        sa.Column("supported_locales", mysql.JSON(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("country_code", sa.CHAR(2), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("address_line1", sa.String(160), nullable=True),
        sa.Column("address_line2", sa.String(160), nullable=True),
        sa.Column("city", sa.String(80), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("email", sa.String(160), nullable=True),
        sa.Column("website", sa.String(160), nullable=True),
        sa.Column("tax_id", sa.String(40), nullable=True),
        sa.Column("registration_number", sa.String(40), nullable=True),
        sa.Column("logo_attachment_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("settings", mysql.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_clinic"),
        sa.UniqueConstraint("public_id", name="uq_clinic__public_id"),
        sa.UniqueConstraint("slug", name="uq_clinic__slug"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "user",
        *_common_columns(),
        sa.Column("email", _CS_190, nullable=False),
        sa.Column("email_verified_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("password_changed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("title", sa.String(40), nullable=True),
        sa.Column("specialty", sa.String(80), nullable=True),
        sa.Column("license_number", sa.String(60), nullable=True),
        sa.Column("signature_attachment_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("preferred_locale", sa.String(10), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("mfa_secret", mysql.VARBINARY(255), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("last_login_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "failed_login_count",
            sa.SmallInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user"),
        sa.UniqueConstraint("public_id", name="uq_user__public_id"),
        sa.UniqueConstraint("email", name="uq_user__email"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "site",
        *_common_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address_line1", sa.String(160), nullable=True),
        sa.Column("address_line2", sa.String(160), nullable=True),
        sa.Column("city", sa.String(80), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_site__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_site"),
        sa.UniqueConstraint("public_id", name="uq_site__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_site__clinic_id", "site", ["clinic_id"])

    op.create_table(
        "permission",
        *_common_columns(),
        sa.Column("code", _CS_80, nullable=False),
        sa.Column("group_code", sa.String(40), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_permission"),
        sa.UniqueConstraint("public_id", name="uq_permission__public_id"),
        sa.UniqueConstraint("code", name="uq_permission__code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "role",
        *_common_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("code", _CS_40, nullable=False),
        sa.Column("name_key", sa.String(80), nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_role__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_role"),
        sa.UniqueConstraint("public_id", name="uq_role__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_role__clinic_id__code", "role", ["clinic_id", "code"])

    op.create_table(
        "role_permission",
        *_common_columns(),
        sa.Column("role_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("permission_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role.id"],
            name="fk_role_permission__role",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name="fk_role_permission__permission",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_role_permission"),
        sa.UniqueConstraint("public_id", name="uq_role_permission__public_id"),
        sa.UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission__role_id__permission_id",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "user_clinic_role",
        *_common_columns(),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("role_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("site_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_user_clinic_role__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_user_clinic_role__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role.id"],
            name="fk_user_clinic_role__role",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["site.id"],
            name="fk_user_clinic_role__site",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_clinic_role"),
        sa.UniqueConstraint("public_id", name="uq_user_clinic_role__public_id"),
        sa.UniqueConstraint(
            "user_id",
            "clinic_id",
            "role_id",
            name="uq_user_clinic_role__user_id__clinic_id__role_id",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_user_clinic_role__clinic_id__user_id",
        "user_clinic_role",
        ["clinic_id", "user_id"],
    )

    op.create_table(
        "user_session",
        *_common_columns(),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("refresh_token_hash", _CS_64, nullable=False),
        sa.Column("device_label", sa.String(120), nullable=True),
        sa.Column("ip_address", mysql.VARBINARY(16), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("issued_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("revoked_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_user_session__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_session"),
        sa.UniqueConstraint("public_id", name="uq_user_session__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_user_session__user_id__expires_at",
        "user_session",
        ["user_id", "expires_at"],
    )


def downgrade() -> None:
    op.drop_table("user_session")
    op.drop_table("user_clinic_role")
    op.drop_table("role_permission")
    op.drop_table("role")
    op.drop_table("permission")
    op.drop_table("site")
    op.drop_table("user")
    op.drop_table("clinic")
