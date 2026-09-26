from __future__ import annotations

import os

import pytest

from tests.support.env import VALID_ENV, clear_settings_cache


@pytest.fixture(autouse=True)
def _configure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fill missing settings; never override CI/service-container credentials."""

    for key, value in VALID_ENV.items():
        if not os.environ.get(key):
            monkeypatch.setenv(key, value)
    clear_settings_cache()


@pytest.fixture(autouse=True)
async def _reset_async_clients() -> None:
    """Avoid cross-test event-loop reuse of the global async engine/Redis client."""

    yield
    from ent.core.db.session import dispose_engine
    from ent.integrations.redis import close_redis

    await dispose_engine()
    await close_redis()
