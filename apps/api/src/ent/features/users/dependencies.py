"""Users FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.features.users.access import AccountAccessService
from ent.features.users.service import UserAdminService


def get_user_admin_service(
    session: AsyncSession = Depends(get_session),
) -> UserAdminService:
    return UserAdminService(session=session)


def get_account_access_service(
    session: AsyncSession = Depends(get_session),
) -> AccountAccessService:
    return AccountAccessService(session=session)
