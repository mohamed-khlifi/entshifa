"""Alembic migration gate: empty database and incremental upgrade (architecture §37)."""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

API_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    return Config(str(API_ROOT / "alembic.ini"))


def _sync_url() -> str:
    from ent.settings import get_settings

    async_url = get_settings().database_url
    if async_url.startswith("mysql+aiomysql://"):
        return "mysql+pymysql://" + async_url.removeprefix("mysql+aiomysql://")
    return async_url


def _assert_mysql_reachable(engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def _upgrade_from_empty(cfg: Config) -> None:
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


def _upgrade_from_previous_revision(cfg: Config) -> None:
    script = ScriptDirectory.from_config(cfg)
    revisions = list(script.walk_revisions())
    if len(revisions) < 2:
        return
    previous = revisions[1].revision
    command.downgrade(cfg, "base")
    command.upgrade(cfg, previous)
    command.upgrade(cfg, "head")


def main() -> int:
    cfg = _alembic_config()
    engine = create_engine(_sync_url())
    try:
        _assert_mysql_reachable(engine)
    except Exception as exc:  # noqa: BLE001 — CI reports connectivity
        print(f"MySQL not reachable for migration check: {exc}", file=sys.stderr)
        return 1

    try:
        _upgrade_from_empty(cfg)
        _upgrade_from_previous_revision(cfg)
    except Exception as exc:  # noqa: BLE001
        print(f"Migration check failed: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print("migration check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
