"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from ent.core.security.cookies import (
    REFRESH_TOKEN_COOKIE,
    clear_refresh_cookie,
    set_refresh_cookie,
)
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.features.auth.dependencies import (
    get_auth_service,
    get_client_ip,
    get_current_user,
    require,
)
from ent.features.auth.schemas.requests import LoginRequest
from ent.features.auth.schemas.responses import LoginResponse, MeResponse
from ent.features.auth.service import AuthService
from ent.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
    ip_address: str | None = Depends(get_client_ip),
) -> LoginResponse:
    payload, raw_refresh = await auth_service.login(
        email=str(body.email),
        password=body.password,
        ip_address=ip_address,
        user_agent=http_request.headers.get("user-agent"),
    )
    set_refresh_cookie(response, settings=settings, raw_token=raw_refresh)
    return payload


@router.post("/refresh", response_model=LoginResponse)
async def refresh_tokens(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
    raw_refresh: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
) -> LoginResponse:
    if raw_refresh is None:
        from ent.core.errors.exceptions import AuthenticationError

        raise AuthenticationError()
    payload, new_refresh = await auth_service.refresh(raw_refresh_token=raw_refresh)
    set_refresh_cookie(response, settings=settings, raw_token=new_refresh)
    return payload


@router.post("/logout")
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
    raw_refresh: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
) -> Response:
    if raw_refresh is not None:
        await auth_service.logout(raw_refresh_token=raw_refresh)
    http_response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(http_response)
    return http_response


@router.get("/me", response_model=MeResponse)
async def read_session(
    user: CurrentUser = Depends(require(Permission.AUTH_SESSION_READ)),
) -> MeResponse:
    return MeResponse(
        user_public_id=user.user_public_id,
        clinic_public_id=user.clinic_public_id,
        permissions=sorted(user.permissions),
    )


@router.get("/clinic-access/{clinic_public_id}")
async def assert_clinic_access(
    clinic_public_id: str,
    user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    await auth_service.assert_clinic_membership_or_not_found(
        user_id=user.user_id,
        clinic_public_id=clinic_public_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/admin-check")
async def admin_check(
    _user: CurrentUser = Depends(require(Permission.ADMIN_USERS)),
) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
