"""Integration: Alembic upgrade/downgrade and concurrent ULID inserts."""

from __future__ import annotations

import concurrent.futures
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from alembic import command
from alembic.config import Config
from ent.core.utils.ids import new_ulid
from ent.settings import get_settings

API_ROOT = Path(__file__).resolve().parents[2]

IDENTITY_TABLES = {
    "clinic",
    "site",
    "user",
    "role",
    "permission",
    "role_permission",
    "user_clinic_role",
    "user_session",
}


def _alembic_config() -> Config:
    return Config(str(API_ROOT / "alembic.ini"))


_PROBE = "entshifa_migration_ci"


def _sync_url() -> str:
    async_url = get_settings().database_url
    if async_url.startswith("mysql+aiomysql://"):
        return "mysql+pymysql://" + async_url.removeprefix("mysql+aiomysql://")
    return async_url


def _root_engine():
    settings = get_settings()
    url = (
        "mysql+pymysql://root:"
        + quote_plus(settings.mysql_root_password)
        + f"@{settings.mysql_host}:{settings.mysql_port}/mysql"
    )
    return create_engine(url, isolation_level="AUTOCOMMIT")


def _probe_url(driver: str) -> str:
    settings = get_settings()
    return (
        f"mysql+{driver}://root:"
        + quote_plus(settings.mysql_root_password)
        + f"@{settings.mysql_host}:{settings.mysql_port}/{_PROBE}"
    )


def _alembic_on_probe(*args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = _probe_url("aiomysql")
    completed = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=API_ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(f"alembic {' '.join(args)} failed on {_PROBE}")


@pytest.mark.integration
def test_migration_upgrade_and_downgrade() -> None:
    """Upgrade and downgrade a private schema. The clinic database is never used."""

    settings = get_settings()
    if settings.mysql_database == _PROBE:
        pytest.fail("disposable schema name matches the application database")
    root = _root_engine()
    try:
        with root.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — skip if Docker MySQL is down
        pytest.skip(f"MySQL not reachable: {exc}")

    with root.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS `{_PROBE}`"))
        connection.execute(
            text(
                f"CREATE DATABASE `{_PROBE}` CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_0900_ai_ci"
            )
        )
    probe = create_engine(_probe_url("pymysql"))
    try:
        _alembic_on_probe("upgrade", "head")
        assert set(inspect(probe).get_table_names()) >= IDENTITY_TABLES

        _alembic_on_probe("downgrade", "base")
        assert IDENTITY_TABLES.isdisjoint(set(inspect(probe).get_table_names()))

        _alembic_on_probe("upgrade", "head")
        assert set(inspect(probe).get_table_names()) >= IDENTITY_TABLES
    finally:
        probe.dispose()
        with root.connect() as connection:
            current = connection.execute(text("SELECT DATABASE()")).scalar()
            if current == settings.mysql_database:
                raise AssertionError("refusing to drop the application database")
            connection.execute(text(f"DROP DATABASE IF EXISTS `{_PROBE}`"))
        root.dispose()


@pytest.mark.integration
def test_ulid_unique_under_concurrent_insert() -> None:
    cfg = _alembic_config()
    engine = create_engine(_sync_url())

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"MySQL not reachable: {exc}")

    command.upgrade(cfg, "head")

    workers = 4
    per_worker = 25

    def _insert_batch(_: int) -> list[str]:
        ids: list[str] = []
        with Session(engine) as session:
            for _ in range(per_worker):
                public_id = new_ulid()
                ids.append(public_id)
                session.execute(
                    text("""
                        INSERT INTO permission (
                            public_id, code, group_code,
                            created_at, updated_at, version
                        ) VALUES (
                            :public_id, :code, 'test',
                            UTC_TIMESTAMP(6), UTC_TIMESTAMP(6), 1
                        )
                        """),
                    {"public_id": public_id, "code": f"test.{public_id}"},
                )
            session.commit()
        return ids

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_insert_batch, range(workers)))

    all_ids = [item for batch in results for item in batch]
    assert len(all_ids) == workers * per_worker
    assert len(set(all_ids)) == len(all_ids)

    with Session(engine) as session:
        rows = (
            session.execute(
                text("SELECT public_id FROM permission WHERE group_code = 'test'"),
            )
            .scalars()
            .all()
        )
        assert len(rows) == len(all_ids)
        assert len(set(rows)) == len(rows)
        session.execute(text("DELETE FROM permission WHERE group_code = 'test'"))
        session.commit()
