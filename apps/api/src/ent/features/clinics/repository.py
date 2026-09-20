"""Clinic feature repository (Site proves tenant scoping for P0-06)."""

from __future__ import annotations

from ent.core.repository.base import BaseRepository
from ent.core.repository.filters import Eq, FilterSet, SearchOn
from ent.features.clinics.models import Site


class SiteFilter(FilterSet):
    search: str | None = SearchOn("name", "city", normalize=True)
    is_primary: bool | None = Eq("is_primary")
    city: str | None = Eq("city")


class SiteRepository(BaseRepository[Site]):
    model = Site
