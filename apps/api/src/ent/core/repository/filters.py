"""Declarative filter builder for list endpoints."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field
from sqlalchemy import Select, func, or_
from sqlalchemy.orm import DeclarativeBase

from ent.core.schemas.base import CamelModel


def Eq(column: str) -> Any:
    return Field(default=None, json_schema_extra={"ent_filter": {"op": "eq", "columns": [column]}})


def Gte(column: str) -> Any:
    return Field(default=None, json_schema_extra={"ent_filter": {"op": "gte", "columns": [column]}})


def Lte(column: str) -> Any:
    return Field(default=None, json_schema_extra={"ent_filter": {"op": "lte", "columns": [column]}})


def SearchOn(*columns: str, normalize: bool = False) -> Any:
    return Field(
        default=None,
        json_schema_extra={
            "ent_filter": {
                "op": "search",
                "columns": list(columns),
                "normalize": normalize,
            },
        },
    )


class FilterSet(CamelModel):
    """Base for declarative filters; subclasses declare fields with Eq/Gte/SearchOn."""

    # Marker so isinstance checks are clear.
    __filter_set__: ClassVar[bool] = True


def apply_filters(
    stmt: Select[Any],
    model: type[DeclarativeBase],
    filters: FilterSet | None,
) -> Select[Any]:
    if filters is None:
        return stmt

    for name, field in filters.__class__.model_fields.items():
        value = getattr(filters, name)
        if value is None:
            continue
        meta = (field.json_schema_extra or {}) if isinstance(field.json_schema_extra, dict) else {}
        spec = meta.get("ent_filter")
        if not isinstance(spec, dict):
            continue
        op = str(spec.get("op", "eq"))
        raw_columns = spec.get("columns", [])
        if not isinstance(raw_columns, list):
            continue
        columns = [str(c) for c in raw_columns]
        if not columns:
            continue

        if op == "eq":
            stmt = stmt.where(getattr(model, columns[0]) == value)
        elif op == "gte":
            stmt = stmt.where(getattr(model, columns[0]) >= value)
        elif op == "lte":
            stmt = stmt.where(getattr(model, columns[0]) <= value)
        elif op == "search":
            term = str(value).strip()
            if not term:
                continue
            pattern = f"%{term}%"
            clauses = []
            for column_name in columns:
                column = getattr(model, column_name)
                if spec.get("normalize"):
                    clauses.append(func.lower(column).like(pattern.lower()))
                else:
                    clauses.append(column.like(pattern))
            stmt = stmt.where(or_(*clauses))
        else:
            msg = f"Unknown filter op: {op}"
            raise ValueError(msg)
    return stmt
