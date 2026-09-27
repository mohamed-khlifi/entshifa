"""Every registered route is classified for tenant isolation."""

from __future__ import annotations

from ent.main import create_app
from ent.settings import get_settings
from tests.api.cross_tenant_catalog import (
    COLLECTION_ROUTES,
    QUERY_TENANT_ROUTES,
    classify_route,
    iter_api_routes,
)


def test_every_route_has_a_tenant_class() -> None:
    app = create_app(settings=get_settings())
    seen = {(method, path) for method, path, _params in iter_api_routes(app)}
    missing_collections = COLLECTION_ROUTES - seen
    missing_queries = QUERY_TENANT_ROUTES - seen
    assert missing_collections == set()
    assert missing_queries == set()

    kinds = {
        classify_route(method, path, params)
        for method, path, params in iter_api_routes(app)
    }
    assert "tenant" in kinds
    assert "collection" in kinds
