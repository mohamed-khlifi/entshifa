"""Auth persistence (sessions, users, permissions)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.auth.models import Permission, Role, RolePermission
from ent.features.clinics.models import Clinic
from ent.features.users.models import User, UserClinicRole, UserSession


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        stmt = select(User).where(
            User.public_id == public_id,
            User.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_clinic_by_public_id(self, public_id: str) -> Clinic | None:
        stmt = select(Clinic).where(
            Clinic.public_id == public_id,
            Clinic.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_clinic_by_id(self, clinic_id: int) -> Clinic | None:
        stmt = select(Clinic).where(
            Clinic.id == clinic_id,
            Clinic.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_session_by_public_id(self, public_id: str) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.public_id == public_id,
            UserSession.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_session_by_refresh_hash(self, token_hash: str) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def find_replayed_session(self, token_hash: str) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.previous_refresh_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def revoke_session_family(self, session_family_id: str, *, at: datetime) -> None:
        stmt = (
            update(UserSession)
            .where(
                UserSession.session_family_id == session_family_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=at)
        )
        await self._session.execute(stmt)

    async def revoke_session(self, session_id: int, *, at: datetime) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(revoked_at=at)
        )
        await self._session.execute(stmt)

    async def update_session_active_clinic(
        self,
        session_id: int,
        clinic_id: int,
    ) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(active_clinic_id=clinic_id)
        )
        await self._session.execute(stmt)

    async def rotate_refresh_token(
        self,
        session_id: int,
        *,
        previous_hash: str,
        new_hash: str,
    ) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(
                previous_refresh_token_hash=previous_hash,
                refresh_token_hash=new_hash,
            )
        )
        await self._session.execute(stmt)

    async def create_session(self, session: UserSession) -> UserSession:
        self._session.add(session)
        await self._session.flush()
        return session

    async def record_failed_login(self, user_id: int) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(failed_login_count=User.failed_login_count + 1)
        )
        await self._session.execute(stmt)

    async def record_successful_login(self, user_id: int, *, at: datetime) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_count=0,
                last_login_at=at,
            )
        )
        await self._session.execute(stmt)

    async def default_clinic_for_user(self, user_id: int) -> Clinic | None:
        today = date.today()
        stmt: Select[tuple[Clinic]] = (
            select(Clinic)
            .join(UserClinicRole, UserClinicRole.clinic_id == Clinic.id)
            .where(
                UserClinicRole.user_id == user_id,
                UserClinicRole.deleted_at.is_(None),
                Clinic.deleted_at.is_(None),
                UserClinicRole.starts_on <= today,
                or_(UserClinicRole.ends_on.is_(None), UserClinicRole.ends_on >= today),
            )
            .order_by(UserClinicRole.starts_on.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def user_belongs_to_clinic(self, user_id: int, clinic_id: int) -> bool:
        today = date.today()
        stmt = select(UserClinicRole.id).where(
            UserClinicRole.user_id == user_id,
            UserClinicRole.clinic_id == clinic_id,
            UserClinicRole.deleted_at.is_(None),
            UserClinicRole.starts_on <= today,
            or_(UserClinicRole.ends_on.is_(None), UserClinicRole.ends_on >= today),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def load_permission_codes(self, user_id: int, clinic_id: int) -> frozenset[str]:
        today = date.today()
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserClinicRole, UserClinicRole.role_id == Role.id)
            .where(
                UserClinicRole.user_id == user_id,
                UserClinicRole.clinic_id == clinic_id,
                UserClinicRole.deleted_at.is_(None),
                Permission.deleted_at.is_(None),
                Role.deleted_at.is_(None),
                UserClinicRole.starts_on <= today,
                or_(UserClinicRole.ends_on.is_(None), UserClinicRole.ends_on >= today),
            )
            .distinct()
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return frozenset(rows)

    async def ensure_permission_row(self, code: str, group_code: str) -> Permission:
        stmt = select(Permission).where(Permission.code == code)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        row = Permission(code=code, group_code=group_code)
        self._session.add(row)
        await self._session.flush()
        return row
