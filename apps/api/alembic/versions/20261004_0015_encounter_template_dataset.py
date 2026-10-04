"""Allow encounter_templates in reference_data_version (P2-03).

Revision ID: 20261004_0015
Revises: 20260320_0014
Create Date: 2026-10-04 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261004_0015"
down_revision: str | Sequence[str] | None = "20260320_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREVIOUS = (
    "dataset IN ('formulary','instruments','protocols',"
    "'terminology','permissions','templates')"
)
_NEXT = (
    "dataset IN ('formulary','instruments','protocols',"
    "'terminology','permissions','templates','encounter_templates')"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_reference_data_version__dataset",
        "reference_data_version",
        type_="check",
    )
    op.create_check_constraint(
        "ck_reference_data_version__dataset",
        "reference_data_version",
        _NEXT,
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM reference_data_version WHERE dataset = 'encounter_templates'"
        )
    )
    op.drop_constraint(
        "ck_reference_data_version__dataset",
        "reference_data_version",
        type_="check",
    )
    op.create_check_constraint(
        "ck_reference_data_version__dataset",
        "reference_data_version",
        _PREVIOUS,
    )
