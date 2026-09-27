"""Patient HTTP endpoints (P1-05)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, Query, Response, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.patients.dependencies import (
    get_content_locale,
    get_patient_service,
    require_patient_read,
)
from ent.features.patients.schemas.requests import (
    PatientAllergyCreate,
    PatientCreate,
    PatientFlagCreate,
    PatientFlagUpdate,
    PatientHistoryCreate,
    PatientIdentifierCreate,
    PatientMedicationCreate,
    PatientMergeRequest,
    PatientProblemCreate,
    PatientUpdate,
)
from ent.features.patients.schemas.responses import (
    PatientAllergyRead,
    PatientFlagRead,
    PatientHistoryRead,
    PatientIdentifierRead,
    PatientMedicationRead,
    PatientMergeRead,
    PatientProblemRead,
    PatientRead,
    PatientSummaryRead,
)
from ent.features.patients.service import PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


def _page(limit: int, offset: int) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


def _key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    if idempotency_key is None:
        return None
    return idempotency_key[:80]


@router.get("", response_model=PageSchema[PatientSummaryRead])
async def list_patients(
    search: str | None = Query(default=None, max_length=190),
    birth_date: date | None = Query(default=None),
    sex: str | None = Query(default=None, max_length=10),
    flag_code: str | None = Query(default=None, max_length=60),
    sort: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientSummaryRead]:
    return await service.list_patients(
        user=user,
        search=search,
        birth_date=birth_date,
        sex=sex,
        flag_code=flag_code,
        sort=sort,
        page=_page(limit, offset),
    )


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
    content_locale: str = Depends(get_content_locale),
) -> PatientRead:
    return await service.create_patient(
        user=user,
        body=body,
        idempotency_key=idempotency_key,
        content_locale=content_locale,
    )


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: str,
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
    content_locale: str = Depends(get_content_locale),
) -> PatientRead:
    return await service.get_patient(
        user=user,
        public_id=patient_id,
        content_locale=content_locale,
    )


@router.patch("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: str,
    body: PatientUpdate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    content_locale: str = Depends(get_content_locale),
) -> PatientRead:
    return await service.update_patient(
        user=user,
        public_id=patient_id,
        body=body,
        content_locale=content_locale,
    )


@router.post("/{patient_id}/merge", response_model=PatientMergeRead)
async def merge_patient(
    patient_id: str,
    body: PatientMergeRequest,
    user: CurrentUser = Depends(require(Permission.PATIENT_MERGE)),
    service: PatientService = Depends(get_patient_service),
) -> PatientMergeRead:
    return await service.merge_patients(user=user, public_id=patient_id, body=body)


@router.get("/{patient_id}/timeline", response_model=PageSchema[PatientSummaryRead])
async def patient_timeline(
    patient_id: str,
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientSummaryRead]:
    return await service.timeline(user=user, public_id=patient_id)


@router.get(
    "/{patient_id}/identifiers",
    response_model=PageSchema[PatientIdentifierRead],
)
async def list_identifiers(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientIdentifierRead]:
    return await service.list_identifiers(
        user=user, public_id=patient_id, page=_page(limit, offset)
    )


@router.post(
    "/{patient_id}/identifiers",
    response_model=PatientIdentifierRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_identifier(
    patient_id: str,
    body: PatientIdentifierCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
) -> PatientIdentifierRead:
    return await service.add_identifier(
        user=user,
        public_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.delete(
    "/{patient_id}/identifiers/{identifier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_identifier(
    patient_id: str,
    identifier_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    await service.delete_identifier(
        user=user,
        public_id=patient_id,
        identifier_id=identifier_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/allergies", response_model=PageSchema[PatientAllergyRead])
async def list_allergies(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientAllergyRead]:
    return await service.list_allergies(
        user=user, public_id=patient_id, page=_page(limit, offset)
    )


@router.post(
    "/{patient_id}/allergies",
    response_model=PatientAllergyRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_allergy(
    patient_id: str,
    body: PatientAllergyCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
) -> PatientAllergyRead:
    return await service.add_allergy(
        user=user,
        public_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.delete(
    "/{patient_id}/allergies/{allergy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_allergy(
    patient_id: str,
    allergy_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    await service.delete_allergy(
        user=user,
        public_id=patient_id,
        allergy_id=allergy_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{patient_id}/medications",
    response_model=PageSchema[PatientMedicationRead],
)
async def list_medications(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientMedicationRead]:
    return await service.list_medications(
        user=user, public_id=patient_id, page=_page(limit, offset)
    )


@router.post(
    "/{patient_id}/medications",
    response_model=PatientMedicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_medication(
    patient_id: str,
    body: PatientMedicationCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
) -> PatientMedicationRead:
    return await service.add_medication(
        user=user,
        public_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.delete(
    "/{patient_id}/medications/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_medication(
    patient_id: str,
    medication_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    await service.delete_medication(
        user=user,
        public_id=patient_id,
        medication_id=medication_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/flags", response_model=PageSchema[PatientFlagRead])
async def list_flags(
    patient_id: str,
    flag_code: str | None = Query(default=None, max_length=60),
    active_only: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientFlagRead]:
    return await service.list_flags(
        user=user,
        public_id=patient_id,
        flag_code=flag_code,
        active_only=active_only,
        page=_page(limit, offset),
    )


@router.post(
    "/{patient_id}/flags",
    response_model=PatientFlagRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_flag(
    patient_id: str,
    body: PatientFlagCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
) -> PatientFlagRead:
    return await service.add_flag(
        user=user,
        public_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.patch("/{patient_id}/flags/{flag_id}", response_model=PatientFlagRead)
async def update_flag(
    patient_id: str,
    flag_id: str,
    body: PatientFlagUpdate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
) -> PatientFlagRead:
    return await service.update_flag(
        user=user, public_id=patient_id, flag_id=flag_id, body=body
    )


@router.get("/{patient_id}/problems", response_model=PageSchema[PatientProblemRead])
async def list_problems(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientProblemRead]:
    return await service.list_problems(
        user=user, public_id=patient_id, page=_page(limit, offset)
    )


@router.post(
    "/{patient_id}/problems",
    response_model=PatientProblemRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_problem(
    patient_id: str,
    body: PatientProblemCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
) -> PatientProblemRead:
    return await service.add_problem(
        user=user,
        public_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.delete(
    "/{patient_id}/problems/{problem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_problem(
    patient_id: str,
    problem_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    await service.delete_problem(
        user=user,
        public_id=patient_id,
        problem_id=problem_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/history", response_model=PageSchema[PatientHistoryRead])
async def list_history(
    patient_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_patient_read()),
    service: PatientService = Depends(get_patient_service),
) -> PageSchema[PatientHistoryRead]:
    return await service.list_history(
        user=user, public_id=patient_id, page=_page(limit, offset)
    )


@router.post(
    "/{patient_id}/history",
    response_model=PatientHistoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_history(
    patient_id: str,
    body: PatientHistoryCreate,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
    idempotency_key: str | None = Depends(_key),
) -> PatientHistoryRead:
    return await service.add_history(
        user=user,
        public_id=patient_id,
        body=body,
        idempotency_key=idempotency_key,
    )


@router.delete(
    "/{patient_id}/history/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_history(
    patient_id: str,
    history_id: str,
    user: CurrentUser = Depends(require(Permission.PATIENT_WRITE)),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    await service.delete_history(
        user=user,
        public_id=patient_id,
        history_id=history_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
