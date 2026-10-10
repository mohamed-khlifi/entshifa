"""Prescription, formulary, and dosing endpoints (P2-08)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.encounters.dependencies import get_content_locale
from ent.features.prescriptions.dependencies import get_prescription_service
from ent.features.prescriptions.schemas.requests import (
    FormularyEntryCreate,
    FormularyEntryUpdate,
    PediatricDoseRequest,
    PrescriptionCreate,
    PrescriptionTemplateCreate,
    PrescriptionUpdate,
    SafetyCheckRequest,
    TaperRequest,
)
from ent.features.prescriptions.schemas.responses import (
    CalculationRead,
    DrugRead,
    FormularyEntryRead,
    PrescriptionRead,
    PrescriptionTemplateRead,
    SafetyAlertRead,
)
from ent.features.prescriptions.service import PrescriptionService

router = APIRouter(tags=["prescriptions"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


def _key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    if idempotency_key is None:
        return None
    return idempotency_key[:80]


@router.get("/api/v1/drugs", response_model=PageSchema[DrugRead])
async def search_drugs(
    q: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[DrugRead]:
    return await service.search_drugs(
        user=user, q=q, page=_page(limit, offset), content_locale=content_locale
    )


@router.get("/api/v1/formulary", response_model=PageSchema[FormularyEntryRead])
async def list_formulary(
    q: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[FormularyEntryRead]:
    return await service.list_formulary(
        user=user, q=q, page=_page(limit, offset), content_locale=content_locale
    )


@router.post(
    "/api/v1/formulary",
    response_model=FormularyEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_formulary_entry(
    body: FormularyEntryCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> FormularyEntryRead:
    return await service.create_formulary(
        user=user, body=body, content_locale=content_locale
    )


@router.patch("/api/v1/formulary/{formulary_id}", response_model=FormularyEntryRead)
async def update_formulary_entry(
    formulary_id: str,
    body: FormularyEntryUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_CLINIC)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> FormularyEntryRead:
    return await service.update_formulary(
        user=user, public_id=formulary_id, body=body, content_locale=content_locale
    )


@router.get(
    "/api/v1/prescription-templates",
    response_model=PageSchema[PrescriptionTemplateRead],
)
async def list_prescription_templates(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PageSchema[PrescriptionTemplateRead]:
    return await service.list_templates(user=user, page=_page(limit, offset))


@router.post(
    "/api/v1/prescription-templates",
    response_model=PrescriptionTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription_template(
    body: PrescriptionTemplateCreate,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionTemplateRead:
    return await service.create_template(user=user, body=body)


@router.get(
    "/api/v1/patients/{patient_id}/prescriptions",
    response_model=PageSchema[PrescriptionRead],
)
async def list_patient_prescriptions(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PageSchema[PrescriptionRead]:
    return await service.list_for_patient(
        user=user,
        patient_public_id=patient_id,
        page=_page(limit, offset),
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/patients/{patient_id}/prescriptions",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription(
    patient_id: str,
    body: PrescriptionCreate,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
    idempotency_key: str | None = Depends(_key),
) -> PrescriptionRead:
    return await service.create(
        user=user,
        patient_public_id=patient_id,
        body=body,
        content_locale=content_locale,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/api/v1/patients/{patient_id}/prescriptions/check-safety",
    response_model=list[SafetyAlertRead],
)
async def check_prescription_safety(
    patient_id: str,
    body: SafetyCheckRequest,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
) -> list[SafetyAlertRead]:
    return await service.check_safety(
        user=user, patient_public_id=patient_id, body=body
    )


@router.post(
    "/api/v1/patients/{patient_id}/prescriptions/calculate-dose",
    response_model=CalculationRead,
)
async def calculate_pediatric_dose(
    patient_id: str,
    body: PediatricDoseRequest,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
) -> CalculationRead:
    return await service.calculate_dose(
        user=user, patient_public_id=patient_id, body=body
    )


@router.post(
    "/api/v1/patients/{patient_id}/prescriptions/generate-taper",
    response_model=CalculationRead,
)
async def generate_prescription_taper(
    patient_id: str,
    body: TaperRequest,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
) -> CalculationRead:
    return await service.generate_taper(
        user=user, patient_public_id=patient_id, body=body
    )


@router.get("/api/v1/prescriptions/{prescription_id}", response_model=PrescriptionRead)
async def get_prescription(
    prescription_id: str,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PrescriptionRead:
    return await service.get(
        user=user, public_id=prescription_id, content_locale=content_locale
    )


@router.patch(
    "/api/v1/prescriptions/{prescription_id}", response_model=PrescriptionRead
)
async def update_prescription(
    prescription_id: str,
    body: PrescriptionUpdate,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_CREATE)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PrescriptionRead:
    return await service.update(
        user=user,
        public_id=prescription_id,
        body=body,
        content_locale=content_locale,
    )


@router.post(
    "/api/v1/prescriptions/{prescription_id}/issue",
    response_model=PrescriptionRead,
)
async def issue_prescription(
    prescription_id: str,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_SIGN)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PrescriptionRead:
    return await service.issue(
        user=user, public_id=prescription_id, content_locale=content_locale
    )


@router.post(
    "/api/v1/prescriptions/{prescription_id}/cancel",
    response_model=PrescriptionRead,
)
async def cancel_prescription(
    prescription_id: str,
    user: CurrentUser = Depends(require(Permission.PRESCRIPTION_SIGN)),
    service: PrescriptionService = Depends(get_prescription_service),
    content_locale: str = Depends(get_content_locale),
) -> PrescriptionRead:
    return await service.cancel(
        user=user, public_id=prescription_id, content_locale=content_locale
    )
