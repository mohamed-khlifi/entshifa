"""Create attachment and media_variant tables (architecture §25.16 / P0-13)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260320_0006"
down_revision: str | Sequence[str] | None = "20260320_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS = "utf8mb4_0900_as_cs"


def _clinical_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
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
            server_default=sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
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
        "attachment",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("procedure_record_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("storage_key", sa.String(400), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("checksum_sha256", sa.String(64, collation=_CS), nullable=True),
        sa.Column("width", sa.SmallInteger(), nullable=True),
        sa.Column("height", sa.SmallInteger(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("body_site_concept_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("laterality", sa.String(10), nullable=True),
        sa.Column("map_region_code", sa.String(80), nullable=True),
        sa.Column("captured_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("captured_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("device", sa.String(80), nullable=True),
        sa.Column("caption", sa.String(255), nullable=True),
        sa.Column(
            "is_consented_for_teaching",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("virus_scanned_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "processing_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("patient_public_id", sa.String(26, collation=_CS), nullable=True),
        sa.CheckConstraint(
            "category IN ('endoscopy_image','endoscopy_video','clinical_photo',"
            "'audiogram_scan','imaging_report','pathology','external_letter',"
            "'document_pdf','signature','logo','voice_recording')",
            name="ck_attachment__category",
        ),
        sa.CheckConstraint(
            "laterality IS NULL OR laterality IN "
            "('right','left','bilateral','midline','na')",
            name="ck_attachment__laterality",
        ),
        sa.CheckConstraint(
            "processing_status IN ('pending','processing','ready','failed')",
            name="ck_attachment__processing_status",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_attachment__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attachment"),
        sa.UniqueConstraint("public_id", name="uq_attachment__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_attachment__clinic_id__patient_id__category__captured_at",
        "attachment",
        ["clinic_id", "patient_id", "category", "captured_at"],
    )
    op.create_index(
        "ix_attachment__clinic_id__storage_key",
        "attachment",
        ["clinic_id", "storage_key"],
        unique=True,
    )
    op.create_index("ix_attachment__clinic_id", "attachment", ["clinic_id"])

    op.create_table(
        "media_variant",
        *_clinical_columns(),
        sa.Column("attachment_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("variant", sa.String(20), nullable=False),
        sa.Column("storage_key", sa.String(400), nullable=False),
        sa.Column("width", sa.SmallInteger(), nullable=True),
        sa.Column("height", sa.SmallInteger(), nullable=True),
        sa.Column("size_bytes", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.CheckConstraint(
            "variant IN ('thumb','preview','web','print')",
            name="ck_media_variant__variant",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_media_variant__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["attachment_id"],
            ["attachment.id"],
            name="fk_media_variant__attachment",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_media_variant"),
        sa.UniqueConstraint("public_id", name="uq_media_variant__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_media_variant__attachment_id__variant",
        "media_variant",
        ["attachment_id", "variant"],
        unique=True,
    )
    op.create_index("ix_media_variant__clinic_id", "media_variant", ["clinic_id"])


def downgrade() -> None:
    op.drop_table("media_variant")
    op.drop_table("attachment")
