from __future__ import annotations

import pytest

from tests.support.env import VALID_ENV, clear_settings_cache


@pytest.fixture(autouse=True)
def _configure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)
    clear_settings_cache()
