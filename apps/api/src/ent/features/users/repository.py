"""User, role, invitation and password-reset persistence."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.repository.pagination import Page, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.auth.models import Permission, Role, RolePermission
from ent.features.clinics.models import Clinic
from ent.features.users.models import (
    PasswordResetToken,
    User,
    UserClinicRole,
    UserInvitation,
)


class UserAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _active_membership(self, today: date) -> tuple[ColumnElement[bool], ...]:
        return (
            UserClinicRole.deleted_at.is_(None),
            UserClinicRole.starts_on <= today,
            or_(UserClinicRole.ends_on.is_(None), UserClinicRole.ends_on >= today),
        )

    async def list_members(
        self,
        *,
        clinic_id: int,
        page: PaginationParams | None,
        search: str | None = None,
    ) -> Page[User]:
        resolved = normalize_pagination(page)
        today = date.today()
        base = (
            select(User)
            .join(UserClinicRole, UserClinicRole.user_id == User.id)
            .where(
                UserClinicRole.clinic_id == clinic_id,
                User.deleted_at.is_(None),
                *self._active_membership(today),
            )
            .distinct()
        )
        if search:
            term = f"%{search.strip()}%"
            base = base.where(
                or_(
                    User.email.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                ),
            )
        total = (
            await self.session.execute(
                select(func.count()).select_from(base.subquery()),
            )
        ).scalar_one()
        offset = resolved.offset or 0
        rows = list(
            (
                await self.session.scalars(
                    base.order_by(User.last_name, User.first_name, User.id)
                    .offset(offset)
                    .limit(resolved.limit),
                )
            ).all()
        )
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=offset,
        )

    async def get_member(self, *, clinic_id: int, public_id: str) -> User | None:
        today = date.today()
        stmt = (
            select(User)
            .join(UserClinicRole, UserClinicRole.user_id == User.id)
            .where(
                User.public_id == public_id,
                User.deleted_at.is_(None),
                UserClinicRole.clinic_id == clinic_id,
                *self._active_membership(today),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def active_role_codes(self, *, clinic_id: int, user_id: int) -> list[str]:
        today = date.today()
        stmt = (
            select(Role.code)
            .join(UserClinicRole, UserClinicRole.role_id == Role.id)
            .where(
                UserClinicRole.user_id == user_id,
                UserClinicRole.clinic_id == clinic_id,
                Role.deleted_at.is_(None),
                *self._active_membership(today),
            )
            .order_by(Role.code)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def membership(
        self,
        *,
        clinic_id: int,
        user_id: int,
        role_id: int,
    ) -> UserClinicRole | None:
        stmt = select(UserClinicRole).where(
            UserClinicRole.clinic_id == clinic_id,
            UserClinicRole.user_id == user_id,
            UserClinicRole.role_id == role_id,
            UserClinicRole.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_roles(self, clinic_id: int) -> list[Role]:
        stmt = (
            select(Role)
            .where(Role.clinic_id == clinic_id, Role.deleted_at.is_(None))
            .order_by(Role.is_system.desc(), Role.code)
        )
        return list((await self.session.scalars(stmt)).all())

    async def get_role(self, *, clinic_id: int, public_id: str) -> Role | None:
        stmt = select(Role).where(
            Role.public_id == public_id,
            Role.clinic_id == clinic_id,
            Role.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_role_by_code(self, *, clinic_id: int, code: str) -> Role | None:
        stmt = select(Role).where(
            Role.clinic_id == clinic_id,
            Role.code == code,
            Role.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def permission_codes_for_role(self, role_id: int) -> list[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == role_id,
                RolePermission.deleted_at.is_(None),
                Permission.deleted_at.is_(None),
            )
            .order_by(Permission.code)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_permissions(self) -> list[Permission]:
        stmt = (
            select(Permission)
            .where(Permission.deleted_at.is_(None))
            .order_by(Permission.code)
        )
        return list((await self.session.scalars(stmt)).all())

    async def permissions_by_codes(self, codes: list[str]) -> list[Permission]:
        if not codes:
            return []
        stmt = select(Permission).where(
            Permission.code.in_(codes),
            Permission.deleted_at.is_(None),
        )
        return list((await self.session.scalars(stmt)).all())

    async def replace_role_permissions(
        self,
        *,
        role_id: int,
        permission_ids: list[int],
    ) -> None:
        existing = list(
            (
                await self.session.scalars(
                    select(RolePermission).where(
                        RolePermission.role_id == role_id,
                        RolePermission.deleted_at.is_(None),
                    ),
                )
            ).all()
        )
        keep = set(permission_ids)
        now = datetime.now(UTC).replace(tzinfo=None)
        for link in existing:
            if link.permission_id not in keep:
                link.deleted_at = now
        present = {link.permission_id for link in existing if link.deleted_at is None}
        from ent.core.utils.ids import new_ulid

        for permission_id in permission_ids:
            if permission_id in present:
                continue
            self.session.add(
                RolePermission(
                    public_id=new_ulid(),
                    role_id=role_id,
                    permission_id=permission_id,
                ),
            )
        await self.session.flush()

    async def clinics_for_user(self, user_id: int) -> list[tuple[Clinic, str]]:
        today = date.today()
        stmt = (
            select(Clinic, Role.code)
            .join(UserClinicRole, UserClinicRole.clinic_id == Clinic.id)
            .join(Role, Role.id == UserClinicRole.role_id)
            .where(
                UserClinicRole.user_id == user_id,
                Clinic.deleted_at.is_(None),
                Role.deleted_at.is_(None),
                *self._active_membership(today),
            )
            .order_by(Clinic.name, Role.code)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(clinic, code) for clinic, code in rows]

    async def get_invitation_by_hash(self, token_hash: str) -> UserInvitation | None:
        stmt = select(UserInvitation).where(
            UserInvitation.token_hash == token_hash,
            UserInvitation.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_reset_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def invalidate_open_resets(self, user_id: int, *, at: datetime) -> None:
        stmt = (
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.deleted_at.is_(None),
            )
            .values(used_at=at)
        )
        await self.session.execute(stmt)
