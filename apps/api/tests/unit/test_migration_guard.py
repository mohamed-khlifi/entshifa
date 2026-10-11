"""Downgrade guard: a database with patients is not disposable."""

from __future__ import annotations

import pytest

from ent.core.db.migration_guard import (
    PopulatedDatabaseError,
    assert_downgrade_allowed,
)


class _Result:
    def __init__(self, value: int) -> None:
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class _Connection:
    def __init__(self, values: list[int]) -> None:
        self._values = values

    def execute(self, _statement: object) -> _Result:
        return _Result(self._values.pop(0))

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


class _Engine:
    def __init__(self, values: list[int]) -> None:
        self._values = values

    def connect(self) -> _Connection:
        return _Connection(self._values)


def test_downgrade_refused_when_patients_exist() -> None:
    engine = _Engine([1, 3])
    with pytest.raises(PopulatedDatabaseError):
        assert_downgrade_allowed(engine)  # type: ignore[arg-type]


def test_downgrade_allowed_when_patient_table_is_absent() -> None:
    engine = _Engine([0])
    assert_downgrade_allowed(engine)  # type: ignore[arg-type]
