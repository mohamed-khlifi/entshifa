"""Offset and cursor pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, asc, desc
from sqlalchemy.orm import DeclarativeBase

from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams

ModelT = TypeVar("ModelT")
SchemaT = TypeVar("SchemaT", bound=BaseModel)

DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 100


@dataclass(frozen=True, slots=True)
class Page(Generic[ModelT]):
    """Internal page result before schema conversion."""

    items: list[ModelT]
    total: int
    limit: int
    offset: int | None = None
    next_cursor: str | None = None

    def to_schema(self, item_schema: type[SchemaT]) -> PageSchema[SchemaT]:
        return PageSchema(
            items=[item_schema.model_validate(row) for row in self.items],
            page=PageMeta(
                total=self.total,
                limit=self.limit,
                offset=self.offset,
                next_cursor=self.next_cursor,
            ),
        )


def normalize_pagination(page: PaginationParams | None) -> PaginationParams:
    """Apply defaults and clamp limit so unbound lists are impossible."""

    if page is None:
        return PaginationParams(limit=DEFAULT_PAGE_LIMIT, offset=0)
    limit = min(max(page.limit, 1), MAX_PAGE_LIMIT)
    if page.cursor:
        return PaginationParams(limit=limit, cursor=page.cursor, offset=None)
    offset = 0 if page.offset is None else page.offset
    return PaginationParams(limit=limit, offset=offset, cursor=None)


def apply_sort(
    stmt: Select[Any],
    model: type[DeclarativeBase],
    sort: str | None,
) -> Select[Any]:
    """Sort string like ``createdAt`` or ``-createdAt`` (camel or snake)."""

    # Clinical models always expose ``id``; DeclarativeBase itself does not.
    id_column = getattr(model, "id")

    if not sort:
        if hasattr(model, "created_at"):
            return stmt.order_by(desc(getattr(model, "created_at")), desc(id_column))
        return stmt.order_by(desc(id_column))

    descending = sort.startswith("-")
    field_name = sort[1:] if descending else sort
    # Accept camelCase from the wire.
    snake = _to_snake(field_name)
    if not hasattr(model, snake):
        snake = "id"
    column = getattr(model, snake)
    return stmt.order_by(desc(column) if descending else asc(column), desc(id_column))


def apply_pagination(stmt: Select[Any], page: PaginationParams) -> Select[Any]:
    resolved = normalize_pagination(page)
    if resolved.cursor is not None:
        # Cursor is the last seen public_id; results are ordered by public_id asc.
        model = stmt.column_descriptions[0]["entity"]
        if hasattr(model, "public_id"):
            stmt = stmt.where(model.public_id > resolved.cursor)
            stmt = stmt.order_by(asc(model.public_id))
        stmt = stmt.limit(resolved.limit)
        return stmt
    offset = resolved.offset or 0
    return stmt.offset(offset).limit(resolved.limit)


def next_cursor_from_rows(rows: list[Any], page: PaginationParams) -> str | None:
    resolved = normalize_pagination(page)
    if resolved.cursor is None:
        return None
    if len(rows) < resolved.limit:
        return None
    last = rows[-1]
    return getattr(last, "public_id", None)


def _to_snake(name: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)
