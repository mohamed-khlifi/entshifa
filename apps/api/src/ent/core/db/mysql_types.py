"""Shared MySQL column type helpers (typed for mypy --strict)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, JSON, VARBINARY


def unsigned_bigint() -> Any:
    return BIGINT(unsigned=True)  # type: ignore[no-untyped-call]


def unsigned_int() -> Any:
    return INTEGER(unsigned=True)  # type: ignore[no-untyped-call]


def datetime6() -> Any:
    return DATETIME(fsp=6)  # type: ignore[no-untyped-call]


def mysql_json() -> Any:
    return JSON()


def varbinary(length: int) -> Any:
    return VARBINARY(length)
