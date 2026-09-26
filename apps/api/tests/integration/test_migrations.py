"""Integration: Alembic upgrade/downgrade and concurrent ULID inserts."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

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


def _sync_url() -> str:
    async_url = get_settings().database_url
    if async_url.startswith("mysql+aiomysql://"):
        return "mysql+pymysql://" + async_url.removeprefix("mysql+aiomysql://")
    return async_url


@pytest.mark.integration
def test_migration_upgrade_and_downgrade() -> None:
    cfg = _alembic_config()
    engine = create_engine(_sync_url())

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — skip if Docker MySQL is down
        pytest.skip(f"MySQL not reachable: {exc}")

    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    inspector = inspect(engine)
    assert set(inspector.get_table_names()) >= IDENTITY_TABLES

    command.downgrade(cfg, "base")
    inspector = inspect(engine)
    assert IDENTITY_TABLES.isdisjoint(set(inspector.get_table_names()))

    command.upgrade(cfg, "head")


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
