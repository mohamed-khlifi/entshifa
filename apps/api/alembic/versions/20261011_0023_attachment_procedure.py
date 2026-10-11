"""Link attachments to procedure_record (P3-05).

Revision ID: 20261011_0023
Revises: 20261011_0022
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20261011_0023"
down_revision: str | Sequence[str] | None = "20261011_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_attachment__procedure_record",
        "attachment",
        "procedure_record",
        ["procedure_record_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_index(
        "ix_attachment__clinic_id__procedure_record_id",
        "attachment",
        ["clinic_id", "procedure_record_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attachment__clinic_id__procedure_record_id",
        table_name="attachment",
    )
    op.drop_constraint(
        "fk_attachment__procedure_record",
        "attachment",
        type_="foreignkey",
    )
