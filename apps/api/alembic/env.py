"""Alembic environment — loads settings and runs sync migrations via PyMySQL."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure `src/` is on the path when Alembic is invoked from apps/api.
_API_ROOT = Path(__file__).resolve().parents[1]
_SRC = _API_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ent.core.db.base import Base  # noqa: E402
from ent.core.db import models_registry as _models_registry  # noqa: E402, F401
from ent.settings import load_settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_database_url(async_url: str) -> str:
    """Convert mysql+aiomysql URL to mysql+pymysql for Alembic's sync runner."""

    if async_url.startswith("mysql+aiomysql://"):
        return "mysql+pymysql://" + async_url.removeprefix("mysql+aiomysql://")
    return async_url


def run_migrations_offline() -> None:
    settings = load_settings()
    url = _sync_database_url(settings.database_url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = load_settings()
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _sync_database_url(settings.database_url)

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
