"""Short office procedures: subtype check and specimen due date (P3-07).

Revision ID: 20261011_0025
Revises: 20261011_0024

Downgrade restores the ear-only subtype check. It fails if a short-procedure
row still exists, because those rows are clinical data and are not deleted.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261011_0025"
down_revision: str | Sequence[str] | None = "20261011_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EAR = (
    "'wax_removal','foreign_body','wick','tube_insertion','tube_removal',"
    "'intratympanic_injection','cavity_cleaning'"
)
_SHORT = (
    "'epistaxis_management','fine_needle_aspiration','oral_pharyngeal_biopsy',"
    "'botulinum_injection','peritonsillar_drainage','nasal_fracture_reduction',"
    "'sialendoscopy'"
)


def upgrade() -> None:
    op.add_column(
        "office_procedure",
        sa.Column("result_due_date", sa.Date(), nullable=True),
    )
    op.drop_constraint(
        "ck_office_procedure__subtype",
        "office_procedure",
        type_="check",
    )
    op.create_check_constraint(
        "ck_office_procedure__subtype",
        "office_procedure",
        f"subtype IN ({_EAR},{_SHORT})",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_office_procedure__subtype",
        "office_procedure",
        type_="check",
    )
    op.create_check_constraint(
        "ck_office_procedure__subtype",
        "office_procedure",
        f"subtype IN ({_EAR})",
    )
    op.drop_column("office_procedure", "result_due_date")
