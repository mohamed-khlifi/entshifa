"""Classify every registered API route for the cross-tenant gate.

A new path parameter that is not listed here fails the unit test, so a
tenant-scoped endpoint cannot ship without an isolation check.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.routing import APIRoute

TENANT_PATH_PARAMS = frozenset(
    {
        "patient_id",
        "site_id",
        "user_id",
        "role_id",
        "appointment_id",
        "type_id",
        "document_id",
        "template_id",
        "public_id",
        "concept_id",
        "identifier_id",
        "allergy_id",
        "medication_id",
        "flag_id",
        "problem_id",
        "history_id",
        "clinic_public_id",
        "encounter_id",
        "encounter_public_id",
        "diagnosis_id",
    }
)

SHARED_PATH_PARAMS = frozenset({"code", "locale"})

# Lists that are scoped to the caller. The integration test proves foreign ids
# are absent. Query-scoped reads (documents, attachments) are tenant routes.
COLLECTION_ROUTES = frozenset(
    {
        ("GET", "/api/v1/patients"),
        ("GET", "/api/v1/sites"),
        ("GET", "/api/v1/users"),
        ("GET", "/api/v1/roles"),
        ("GET", "/api/v1/appointment-types"),
        ("GET", "/api/v1/appointments"),
        ("GET", "/api/v1/appointments/waiting-room"),
        ("GET", "/api/v1/scheduling/doctors"),
        ("GET", "/api/v1/document-templates"),
        ("GET", "/api/v1/auth/clinics"),
        ("GET", "/api/v1/terminology/admin/concepts"),
        ("GET", "/api/v1/terminology/admin/value-sets"),
        ("GET", "/api/v1/terminology/concepts/search"),
        ("GET", "/api/v1/observations/cohort"),
    }
)

QUERY_TENANT_ROUTES = frozenset(
    {
        ("GET", "/api/v1/documents"),
        ("GET", "/api/v1/attachments"),
    }
)

MUTATION_OK = frozenset({400, 404, 422})


def path_params(path: str) -> frozenset[str]:
    return frozenset(raw.split(":", 1)[0] for raw in re.findall(r"\{([^}]+)\}", path))


def iter_api_routes(app: FastAPI) -> Iterator[tuple[str, str, frozenset[str]]]:
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path.startswith(("/docs", "/redoc", "/openapi")):
            continue
        params = path_params(route.path)
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            yield method, route.path, params


def classify_route(method: str, path: str, params: frozenset[str]) -> str:
    unknown = params - TENANT_PATH_PARAMS - SHARED_PATH_PARAMS
    if unknown:
        msg = f"unclassified path params {sorted(unknown)} on {method} {path}"
        raise ValueError(msg)
    if (method, path) in QUERY_TENANT_ROUTES or bool(params & TENANT_PATH_PARAMS):
        return "tenant"
    if (method, path) in COLLECTION_ROUTES:
        return "collection"
    return "unscoped"


def fill_path(path: str, ids: dict[str, str]) -> str:
    """Substitute path parameters. Shared params get harmless reference values."""

    rendered = path
    for name in TENANT_PATH_PARAMS | SHARED_PATH_PARAMS:
        token = "{" + name + "}"
        if token not in rendered:
            continue
        if name == "locale":
            value = "en"
        elif name == "code":
            value = "tm.findings"
        else:
            value = ids[name]
        rendered = rendered.replace(token, value)
    return rendered
