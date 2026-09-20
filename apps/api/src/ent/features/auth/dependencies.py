"""FastAPI dependencies for auth."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.core.errors.exceptions import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
)
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.core.security.tokens import decode_access_token
from ent.features.auth.service import AuthService
from ent.settings import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(session=session, settings=settings)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    clinic_public_id_header: str | None = Header(default=None, alias="X-Clinic-Id"),
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError()

    try:
        payload = decode_access_token(settings, credentials.credentials)
    except Exception as exc:
        raise AuthenticationError() from exc

    session_public_id = str(payload.get("sid", ""))
    user_public_id = str(payload.get("sub", ""))
    token_clinic_public_id = str(payload.get("cid", ""))

    session_row = await auth_service.get_active_session(session_public_id)
    if session_row is None:
        raise AuthenticationError()

    user = await auth_service.get_user_by_public_id(user_public_id)
    if user is None or not user.is_active:
        raise AuthenticationError()

    target_clinic_public_id = clinic_public_id_header or token_clinic_public_id
    if clinic_public_id_header and clinic_public_id_header != token_clinic_public_id:
        await auth_service.assert_clinic_membership_or_not_found(
            user_id=user.id,
            clinic_public_id=clinic_public_id_header,
        )

    clinic = await auth_service.get_clinic_by_public_id(target_clinic_public_id)
    if clinic is None:
        raise NotFoundError(resource="clinic")

    if session_row.active_clinic_id != clinic.id:
        await auth_service.update_session_active_clinic(session_row.id, clinic.id)

    permissions = await auth_service.load_permissions(user.id, clinic.id)

    from ent.core.context import set_clinic_id, set_user_id

    set_user_id(user.id)
    set_clinic_id(clinic.id)

    return CurrentUser(
        user_id=user.id,
        user_public_id=user.public_id,
        session_id=session_row.id,
        session_public_id=session_row.public_id,
        clinic_id=clinic.id,
        clinic_public_id=clinic.public_id,
        permissions=permissions,
    )


def require(
    permission: Permission,
) -> Callable[..., Awaitable[CurrentUser]]:
    async def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission.value not in user.permissions:
            raise PermissionDeniedError(permission=permission.value)
        return user

    return _dependency


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None
