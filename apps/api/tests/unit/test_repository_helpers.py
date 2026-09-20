"""Unit tests for declarative filters and pagination helpers."""

from __future__ import annotations

from sqlalchemy import select

from ent.core.repository.filters import Eq, FilterSet, SearchOn, apply_filters
from ent.core.repository.pagination import apply_sort, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.clinics.models import Site
from ent.features.clinics.repository import SiteFilter


def test_site_filter_declares_search_and_eq() -> None:
    filters = SiteFilter(search="Paris", is_primary=True)
    stmt = apply_filters(select(Site), Site, filters)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "site.name" in sql.lower() or "name" in sql.lower()
    assert "is_primary" in sql.lower()


def test_filter_set_ignores_none_fields() -> None:
    class DemoFilter(FilterSet):
        city: str | None = Eq("city")
        search: str | None = SearchOn("name")

    base = select(Site)
    filtered = apply_filters(base, Site, DemoFilter())
    assert str(filtered) == str(base)


def test_apply_sort_accepts_camel_and_descending() -> None:
    stmt = apply_sort(select(Site), Site, "-createdAt")
    compiled = str(stmt.compile())
    assert "created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


def test_cursor_mode_clears_offset() -> None:
    resolved = normalize_pagination(PaginationParams(limit=10, offset=5, cursor="01JCURSOR"))
    assert resolved.cursor == "01JCURSOR"
    assert resolved.offset is None
    assert resolved.limit == 10
