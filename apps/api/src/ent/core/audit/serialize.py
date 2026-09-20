"""Serialize ORM rows for audit before/after images."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Mapper
from sqlalchemy.orm.attributes import get_history

_REDACTED_KEYS = frozenset(
    {
        "password_hash",
        "mfa_secret",
        "refresh_token_hash",
        "previous_refresh_token_hash",
        "access_token",
    },
)


def row_to_audit_dict(obj: object) -> dict[str, Any]:
    mapper: Mapper[Any] = obj.__mapper__  # type: ignore[attr-defined]
    result: dict[str, Any] = {}
    for column in mapper.columns:
        key = column.key
        if key is None:
            continue
        value = getattr(obj, key, None)
        if key in _REDACTED_KEYS and value is not None:
            result[key] = "[redacted]"
            continue
        result[key] = json_safe(value)
    return result


def changed_field_names(obj: object) -> list[str]:
    mapper: Mapper[Any] = obj.__mapper__  # type: ignore[attr-defined]
    changed: list[str] = []
    for attr in mapper.column_attrs:
        history = get_history(obj, attr.key)
        if history.has_changes():
            changed.append(attr.key)
    return sorted(changed)


def json_safe(value: object) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return str(value)
