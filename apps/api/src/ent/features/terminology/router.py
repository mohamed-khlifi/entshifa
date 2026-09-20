"""Terminology HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.terminology.dependencies import get_terminology_service
from ent.features.terminology.schemas.responses import (
    ConceptDictionaryResponse,
    ConceptSearchResponse,
    ValueSetRead,
)
from ent.features.terminology.service import TerminologyService

router = APIRouter(prefix="/api/v1/terminology", tags=["terminology"])


@router.get("/concepts/search", response_model=ConceptSearchResponse)
async def search_concepts(
    q: str = Query(min_length=1, max_length=120),
    locale: str | None = Query(default=None, max_length=10),
    kind: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ConceptSearchResponse:
    return await service.search_concepts(
        user=user,
        q=q,
        locale=locale,
        kind=kind,
        limit=limit,
        offset=offset,
    )


@router.get("/value-sets/{code}", response_model=ValueSetRead)
async def get_value_set(
    code: str,
    locale: str | None = Query(default=None, max_length=10),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ValueSetRead:
    return await service.get_value_set(user=user, code=code, locale=locale)


@router.get("/dictionary", response_model=ConceptDictionaryResponse)
async def get_dictionary(
    locale: str | None = Query(default=None, max_length=10),
    kinds: str | None = Query(
        default=None,
        description="Comma-separated concept kinds, e.g. anatomy,finding",
    ),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ConceptDictionaryResponse:
    kind_list = [part.strip() for part in kinds.split(",") if part.strip()] if kinds else None
    return await service.get_dictionary(user=user, locale=locale, kinds=kind_list)
