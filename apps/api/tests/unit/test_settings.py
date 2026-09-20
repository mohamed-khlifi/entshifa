from __future__ import annotations

import pytest

from ent.settings import get_settings, load_settings
from tests.support.env import clear_settings_cache


def test_settings_loads_from_environment() -> None:
    clear_settings_cache()
    settings = get_settings()
    assert settings.mysql_database == "entshifa"
    assert settings.cors_origins == ["http://localhost:3000"]


def test_missing_required_env_var_exits_with_clear_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_settings_cache()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "")

    with pytest.raises(SystemExit) as exc_info:
        load_settings()

    message = str(exc_info.value)
    assert "configuration error" in message.lower()


def test_cors_origins_parsed_as_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test,http://b.test")
    clear_settings_cache()
    assert get_settings().cors_origins == ["http://a.test", "http://b.test"]
