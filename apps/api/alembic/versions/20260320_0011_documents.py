"""Document engine tables (architecture §25.12 / P1-09).

Revision ID: 20260320_0011
Revises: 20260320_0010
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20260320_0011"
down_revision: str | Sequence[str] | None = "20260320_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS = "utf8mb4_0900_as_cs"
_CATEGORIES = (
    "'consultation_report','endoscopy_report','audiology_report','prescription',"
    "'certificate','imaging_request','referral_letter','handout','consent',"
    "'quote','operative_note','tumor_board','patient_summary'"
)
_LOCALES = "'en','fr','ar'"


def _global_columns() -> list[sa.Column[object]]:
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
        sa.Column(
            "version",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="1",
        ),
    ]


def _version_columns() -> list[sa.Column[object]]:
    """Template revision rows. ``version`` here is the revision number."""

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
        "document_template",
        *_global_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_clinic_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(clinic_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column("code", sa.String(60, collation=_CS), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("engine", sa.String(20), nullable=False, server_default="html"),
        sa.Column("placeholders", mysql.JSON(), nullable=False),
        sa.Column(
            "is_system",
            mysql.TINYINT(display_width=1),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_active",
            mysql.TINYINT(display_width=1),
            nullable=False,
            server_default="1",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_template"),
        sa.UniqueConstraint("public_id", name="uq_document_template__public_id"),
        sa.UniqueConstraint(
            "scope_clinic_id",
            "code",
            name="uq_document_template__scope_clinic_id__code",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_document_template__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"category IN ({_CATEGORIES})",
            name="ck_document_template__category",
        ),
        sa.CheckConstraint("engine IN ('html')", name="ck_document_template__engine"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_document_template__code",
        "document_template",
        ["code"],
    )

    op.create_table(
        "document_template_version",
        *_version_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("document_template_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("header_html", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("body_html", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("footer_html", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("css", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("page_setup", mysql.JSON(), nullable=False),
        sa.Column("direction", sa.String(3), nullable=False),
        sa.Column("published_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_document_template_version"),
        sa.UniqueConstraint(
            "public_id",
            name="uq_document_template_version__public_id",
        ),
        sa.UniqueConstraint(
            "document_template_id",
            "version",
            "locale",
            name="uq_document_template_version__template__version__locale",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_document_template_version__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_template_id"],
            ["document_template.id"],
            name="fk_document_template_version__document_template",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"locale IN ({_LOCALES})",
            name="ck_document_template_version__locale",
        ),
        sa.CheckConstraint(
            "direction IN ('ltr','rtl')",
            name="ck_document_template_version__direction",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "document",
        *_global_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("template_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("template_version_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("rendered_attachment_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("content_snapshot", mysql.JSON(), nullable=False),
        sa.Column("body_override_html", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column("finalized_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("finalized_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("content_hash", sa.CHAR(64, collation=_CS), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_document"),
        sa.UniqueConstraint("public_id", name="uq_document__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_document__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_document__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["document_template.id"],
            name="fk_document__document_template",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_version_id"],
            ["document_template_version.id"],
            name="fk_document__document_template_version",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["rendered_attachment_id"],
            ["attachment.id"],
            name="fk_document__attachment",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"category IN ({_CATEGORIES})", name="ck_document__category"
        ),
        sa.CheckConstraint(f"locale IN ({_LOCALES})", name="ck_document__locale"),
        sa.CheckConstraint(
            "status IN ('draft','final','cancelled')",
            name="ck_document__status",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_document__clinic_id__patient_id__created_at",
        "document",
        ["clinic_id", "patient_id", "created_at"],
    )
    op.create_index(
        "ix_document__clinic_id__category__status",
        "document",
        ["clinic_id", "category", "status"],
    )

    op.create_table(
        "document_recipient",
        *_global_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("document_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("recipient_type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("address", sa.String(190), nullable=True),
        sa.Column("locale", sa.String(10), nullable=True),
        sa.Column("sent_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "delivery_status",
            sa.String(30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_text", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_document_recipient"),
        sa.UniqueConstraint("public_id", name="uq_document_recipient__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_document_recipient__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name="fk_document_recipient__document",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "recipient_type IN ('patient','referrer','insurer','other')",
            name="ck_document_recipient__recipient_type",
        ),
        sa.CheckConstraint(
            "channel IN ('print','download')",
            name="ck_document_recipient__channel",
        ),
        sa.CheckConstraint(
            "delivery_status IN ('pending','sent','failed')",
            name="ck_document_recipient__delivery_status",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_document_recipient__clinic_id__document_id",
        "document_recipient",
        ["clinic_id", "document_id"],
    )

    op.create_table(
        "phrase_library",
        *_global_columns(),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "scope_user_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed("ifnull(user_id, 0)", persisted=True),
            nullable=False,
        ),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("shortcut", sa.String(20, collation=_CS), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("body", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_phrase_library"),
        sa.UniqueConstraint("public_id", name="uq_phrase_library__public_id"),
        sa.UniqueConstraint(
            "clinic_id",
            "scope_user_id",
            "shortcut",
            "locale",
            name="uq_phrase_library__clinic__user__shortcut__locale",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_phrase_library__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            f"locale IN ({_LOCALES})",
            name="ck_phrase_library__locale",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )


def downgrade() -> None:
    op.drop_table("phrase_library")
    op.drop_table("document_recipient")
    op.drop_table("document")
    op.drop_table("document_template_version")
    op.drop_table("document_template")
