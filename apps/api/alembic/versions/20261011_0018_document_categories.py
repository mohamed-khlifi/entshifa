"""Allow lab_request on document templates (P2-10).

Revision ID: 20261011_0018
Revises: 20261010_0017
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20261011_0018"
down_revision: str | Sequence[str] | None = "20261010_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREVIOUS = (
    "'consultation_report','endoscopy_report','audiology_report','prescription',"
    "'certificate','imaging_request','referral_letter','handout','consent',"
    "'quote','operative_note','tumor_board','patient_summary'"
)
_NEXT = (
    "'consultation_report','endoscopy_report','audiology_report','prescription',"
    "'certificate','imaging_request','lab_request','referral_letter','handout',"
    "'consent','quote','operative_note','tumor_board','patient_summary'"
)


def upgrade() -> None:
    _replace("document_template", "ck_document_template__category", _NEXT)
    _replace("document", "ck_document__category", _NEXT)


def downgrade() -> None:
    _replace("document_template", "ck_document_template__category", _PREVIOUS)
    _replace("document", "ck_document__category", _PREVIOUS)


def _replace(table: str, name: str, categories: str) -> None:
    op.drop_constraint(name, table, type_="check")
    op.create_check_constraint(name, table, f"category IN ({categories})")
