"""Clinic user and role administration (P1-02)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import require
from ent.features.users.access import AccountAccessService
from ent.features.users.dependencies import (
    get_account_access_service,
    get_user_admin_service,
)
from ent.features.users.schemas.requests import (
    CustomRoleCreate,
    CustomRoleUpdate,
    InvitationCreate,
    RoleAssignment,
    UserUpdate,
)
from ent.features.users.schemas.responses import (
    InvitationRead,
    PermissionRead,
    RoleRead,
    UserRead,
)
from ent.features.users.service import UserAdminService

router = APIRouter(tags=["users"])


@router.get("/api/v1/users", response_model=PageSchema[UserRead])
async def list_users(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> PageSchema[UserRead]:
    return await service.list_users(
        user=user,
        page=PaginationParams(limit=limit, offset=offset),
    )


@router.get("/api/v1/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserRead:
    return await service.get_user(user=user, public_id=user_id)


@router.patch("/api/v1/users/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: str,
    body: UserUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserRead:
    return await service.update_user(actor=user, public_id=user_id, body=body)


@router.post("/api/v1/users/{user_id}/roles", response_model=UserRead)
async def assign_role(
    user_id: str,
    body: RoleAssignment,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserRead:
    return await service.assign_role(actor=user, public_id=user_id, body=body)


@router.delete(
    "/api/v1/users/{user_id}/roles/{role_id}",
    response_model=UserRead,
)
async def revoke_role(
    user_id: str,
    role_id: str,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserRead:
    return await service.revoke_role(
        actor=user, public_id=user_id, role_public_id=role_id
    )


@router.get("/api/v1/roles", response_model=list[RoleRead])
async def list_roles(
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> list[RoleRead]:
    return await service.list_roles(user=user)


@router.get("/api/v1/permissions", response_model=list[PermissionRead])
async def list_permissions(
    _user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> list[PermissionRead]:
    return await service.list_permissions()


@router.post(
    "/api/v1/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    body: CustomRoleCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> RoleRead:
    return await service.create_role(actor=user, body=body)


@router.patch("/api/v1/roles/{role_id}", response_model=RoleRead)
async def patch_role(
    role_id: str,
    body: CustomRoleUpdate,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: UserAdminService = Depends(get_user_admin_service),
) -> RoleRead:
    return await service.update_role(actor=user, public_id=role_id, body=body)


@router.post(
    "/api/v1/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    body: InvitationCreate,
    user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
    service: AccountAccessService = Depends(get_account_access_service),
) -> InvitationRead:
    return await service.create_invitation(actor=user, body=body)
