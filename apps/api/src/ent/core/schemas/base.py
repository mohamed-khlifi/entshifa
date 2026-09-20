"""Shared Pydantic bases (architecture section 7 / P0-06)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """Serializes snake_case Python fields to camelCase JSON."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ORMModel(CamelModel):
    """Read model built from ORM attributes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PageMeta(CamelModel):
    """Pagination envelope metadata."""

    total: int | None = None
    limit: int
    offset: int | None = None
    next_cursor: str | None = None


class PageSchema(CamelModel, Generic[T]):
    """Standard list envelope: items + page meta."""

    items: list[T]
    page: PageMeta


class PaginationParams(CamelModel):
    """Incoming pagination; defaults keep every list bounded."""

    limit: int = Field(default=25, ge=1, le=100)
    offset: int | None = Field(default=None, ge=0)
    cursor: str | None = None
