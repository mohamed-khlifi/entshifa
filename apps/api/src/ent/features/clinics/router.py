"""Clinic, site and clinical-settings HTTP endpoints (P1-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.clinics.dependencies import get_clinic_service
from ent.features.clinics.schemas.requests import (
    ClinicalSettingsPut,
    ClinicUpdate,
    SiteCreate,
    SiteUpdate,
)
from ent.features.clinics.schemas.responses import (
    ClinicalSettingsRead,
    ClinicRead,
    SiteRead,
)
from ent.features.clinics.service import ClinicService

router = APIRouter(tags=["clinics"])


@router.get("/api/v1/clinic", response_model=ClinicRead)
async def get_clinic(
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: ClinicService = Depends(get_clinic_service),
) -> ClinicRead:
    return await service.get_current_clinic(user=user)


@router.patch("/api/v1/clinic", response_model=ClinicRead)
async def patch_clinic(
    body: ClinicUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: ClinicService = Depends(get_clinic_service),
) -> ClinicRead:
    return await service.update_current_clinic(user=user, body=body)


@router.get("/api/v1/sites", response_model=PageSchema[SiteRead])
async def list_sites(
    search: str | None = Query(default=None, max_length=120),
    is_primary: bool | None = Query(default=None),
    city: str | None = Query(default=None, max_length=80),
    sort: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: ClinicService = Depends(get_clinic_service),
) -> PageSchema[SiteRead]:
    return await service.list_sites(
        user=user,
        search=search,
        is_primary=is_primary,
        city=city,
        sort=sort,
        page=PaginationParams(limit=limit, offset=offset),
    )


@router.post(
    "/api/v1/sites",
    response_model=SiteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_site(
    body: SiteCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: ClinicService = Depends(get_clinic_service),
) -> SiteRead:
    return await service.create_site(user=user, body=body)


@router.get("/api/v1/sites/{site_id}", response_model=SiteRead)
async def get_site(
    site_id: str,
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: ClinicService = Depends(get_clinic_service),
) -> SiteRead:
    return await service.get_site(user=user, public_id=site_id)


@router.patch("/api/v1/sites/{site_id}", response_model=SiteRead)
async def patch_site(
    site_id: str,
    body: SiteUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: ClinicService = Depends(get_clinic_service),
) -> SiteRead:
    return await service.update_site(user=user, public_id=site_id, body=body)


@router.delete("/api/v1/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: str,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: ClinicService = Depends(get_clinic_service),
) -> Response:
    await service.delete_site(user=user, public_id=site_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/v1/settings/clinical", response_model=ClinicalSettingsRead)
async def get_clinical_settings(
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
    service: ClinicService = Depends(get_clinic_service),
) -> ClinicalSettingsRead:
    return await service.get_clinical_settings(user=user)


@router.put("/api/v1/settings/clinical", response_model=ClinicalSettingsRead)
async def put_clinical_settings(
    body: ClinicalSettingsPut,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: ClinicService = Depends(get_clinic_service),
) -> ClinicalSettingsRead:
    return await service.put_clinical_settings(user=user, body=body)
