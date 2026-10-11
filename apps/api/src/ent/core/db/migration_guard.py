"""Refuse Alembic downgrades against a database that already holds patients."""

from __future__ import annotations

from sqlalchemy import Engine, text

_PATIENT_TABLE = text("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
      AND table_name = 'patient'
    """)
_PATIENT_COUNT = text("SELECT COUNT(*) FROM patient")


class PopulatedDatabaseError(RuntimeError):
    """Downgrade was refused because the database already contains patients."""


def assert_downgrade_allowed(engine: Engine) -> None:
    """Raise before any downgrade when ``patient`` already has rows.

    MySQL commits each DDL statement on its own. A downgrade that fails halfway
    still leaves the earlier drops applied, so this guard never connects that
    path to a clinic database.
    """

    with engine.connect() as connection:
        patient_table = connection.execute(_PATIENT_TABLE).scalar_one()
        if not patient_table:
            return
        patient_count = connection.execute(_PATIENT_COUNT).scalar_one()
    if patient_count:
        raise PopulatedDatabaseError(
            "Refusing to downgrade a database that contains patients."
        )
