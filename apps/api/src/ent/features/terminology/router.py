"""Terminology HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status

from ent.core.schemas.base import PageSchema
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.terminology.dependencies import get_terminology_service
from ent.features.terminology.schemas.requests import (
    ConceptCreate,
    ConceptTranslationUpsert,
    ConceptUpdate,
    ValueSetMemberCreate,
    ValueSetMemberUpdate,
)
from ent.features.terminology.schemas.responses import (
    ConceptAdminRead,
    ConceptDictionaryResponse,
    ConceptSearchResponse,
    TranslationCoverageItem,
    ValueSetRead,
    ValueSetSummaryRead,
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
    kind_list = (
        [part.strip() for part in kinds.split(",") if part.strip()] if kinds else None
    )
    return await service.get_dictionary(user=user, locale=locale, kinds=kind_list)


@router.get("/admin/concepts", response_model=PageSchema[ConceptAdminRead])
async def list_admin_concepts(
    q: str | None = Query(default=None, max_length=120),
    kind: str | None = Query(default=None, max_length=40),
    clinic_owned_only: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> PageSchema[ConceptAdminRead]:
    return await service.list_admin_concepts(
        user=user,
        q=q,
        kind=kind,
        clinic_owned_only=clinic_owned_only,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/admin/concepts",
    response_model=ConceptAdminRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_clinic_concept(
    body: ConceptCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ConceptAdminRead:
    return await service.create_clinic_concept(user=user, body=body)


@router.get("/admin/concepts/{concept_id}", response_model=ConceptAdminRead)
async def get_admin_concept(
    concept_id: str,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ConceptAdminRead:
    return await service.get_admin_concept(user=user, public_id=concept_id)


@router.patch("/admin/concepts/{concept_id}", response_model=ConceptAdminRead)
async def update_clinic_concept(
    concept_id: str,
    body: ConceptUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ConceptAdminRead:
    return await service.update_clinic_concept(
        user=user, public_id=concept_id, body=body
    )


@router.delete("/admin/concepts/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinic_concept(
    concept_id: str,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> Response:
    await service.delete_clinic_concept(user=user, public_id=concept_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/admin/concepts/{concept_id}/translations/{locale}",
    response_model=ConceptAdminRead,
)
async def upsert_clinic_translation(
    concept_id: str,
    locale: str,
    body: ConceptTranslationUpsert,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ConceptAdminRead:
    return await service.upsert_clinic_translation(
        user=user,
        public_id=concept_id,
        locale=locale,
        body=body,
    )


@router.get("/admin/value-sets", response_model=list[ValueSetSummaryRead])
async def list_value_sets(
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> list[ValueSetSummaryRead]:
    return await service.list_value_sets(user=user)


@router.post(
    "/admin/value-sets/{code}/members",
    response_model=ValueSetRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_value_set_member(
    code: str,
    body: ValueSetMemberCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ValueSetRead:
    return await service.add_clinic_value_set_member(user=user, code=code, body=body)


@router.patch(
    "/admin/value-sets/{code}/members/{concept_id}",
    response_model=ValueSetRead,
)
async def update_value_set_member(
    code: str,
    concept_id: str,
    body: ValueSetMemberUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ValueSetRead:
    return await service.update_clinic_value_set_member(
        user=user,
        code=code,
        concept_public_id=concept_id,
        body=body,
    )


@router.delete(
    "/admin/value-sets/{code}/members/{concept_id}",
    response_model=ValueSetRead,
)
async def remove_value_set_member(
    code: str,
    concept_id: str,
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> ValueSetRead:
    return await service.remove_clinic_value_set_member(
        user=user,
        code=code,
        concept_public_id=concept_id,
    )


@router.get(
    "/admin/translation-coverage",
    response_model=PageSchema[TranslationCoverageItem],
)
async def translation_coverage(
    locale: str = Query(min_length=2, max_length=10),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.ADMIN_TERMINOLOGY)),
    service: TerminologyService = Depends(get_terminology_service),
) -> PageSchema[TranslationCoverageItem]:
    return await service.translation_coverage(
        user=user,
        locale=locale,
        limit=limit,
        offset=offset,
    )
