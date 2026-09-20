"""Unit tests for request contextvars."""

from __future__ import annotations

from ent.core.context import (
    get_clinic_id,
    get_request_id,
    get_user_id,
    set_clinic_id,
    set_request_id,
    set_user_id,
)
from ent.core.utils.ids import new_ulid


def test_request_id_defaults_to_ulid() -> None:
    set_request_id("")
    value = get_request_id()
    assert len(value) == 26


def test_user_and_clinic_context() -> None:
    set_user_id(42)
    set_clinic_id(7)
    assert get_user_id() == 42
    assert get_clinic_id() == 7
    set_request_id(new_ulid())
    assert len(get_request_id()) == 26
