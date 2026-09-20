"""SQLAlchemy declarative base and MySQL naming convention (architecture §23)."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Index / constraint names: ix_/uq_/fk_/ck_/pk_ with double-underscore separators.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s__%(column_0_N_name)s",
    "uq": "uq_%(table_name)s__%(column_0_N_name)s",
    "ck": "ck_%(table_name)s__%(constraint_name)s",
    "fk": "fk_%(table_name)s__%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model."""

    metadata = metadata
