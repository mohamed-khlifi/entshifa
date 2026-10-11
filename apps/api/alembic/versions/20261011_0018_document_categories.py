"""Allow lab_request on document templates (P2-10).

Revision ID: 20261011_0018
Revises: 20261010_0017
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

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
    # Rows allowed only by the newer check must go before the check narrows.
    # Otherwise MySQL rejects the replacement. Deletes run first; the check
    # change itself is one atomic ALTER, so a failed replacement keeps the
    # current check.
    _delete_lab_request_rows()
    _replace("document_template", "ck_document_template__category", _PREVIOUS)
    _replace("document", "ck_document__category", _PREVIOUS)


def _stored_check_name(table: str, name: str) -> str:
    """MySQL name after ``ck_<table>__<given name>`` is applied."""

    return f"ck_{table}__{name}"


def _replace(table: str, name: str, categories: str) -> None:
    stored = _stored_check_name(table, name)
    op.execute(
        sa.text(
            f"ALTER TABLE `{table}` "
            f"DROP CHECK `{stored}`, "
            f"ADD CONSTRAINT `{stored}` CHECK (category IN ({categories}))"
        )
    )


def _delete_lab_request_rows() -> None:
    doomed_documents = (
        "SELECT id FROM ("
        "SELECT d.id FROM document d "
        "LEFT JOIN document_template t ON t.id = d.template_id "
        "LEFT JOIN document_template_version v ON v.id = d.template_version_id "
        "LEFT JOIN document_template tv ON tv.id = v.document_template_id "
        "WHERE d.category = 'lab_request' "
        "OR t.category = 'lab_request' "
        "OR tv.category = 'lab_request'"
        ") AS doomed_documents"
    )
    op.execute(
        sa.text(
            "UPDATE prescription SET document_id = NULL "
            f"WHERE document_id IN ({doomed_documents})"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM document_recipient "
            f"WHERE document_id IN ({doomed_documents})"
        )
    )
    op.execute(sa.text(f"DELETE FROM document WHERE id IN ({doomed_documents})"))
    op.execute(
        sa.text(
            "DELETE FROM document_template_version WHERE document_template_id IN ("
            "SELECT id FROM ("
            "SELECT id FROM document_template WHERE category = 'lab_request'"
            ") AS doomed_templates)"
        )
    )
    op.execute(sa.text("DELETE FROM document_template WHERE category = 'lab_request'"))
