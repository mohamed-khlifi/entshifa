"""Clinic user, role and invitation use cases (P1-02)."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import ConflictError, NotFoundError, ValidationError
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.auth.models import Permission, Role
from ent.features.clinics.repository import SiteRepository
from ent.features.users.models import User, UserClinicRole
from ent.features.users.repository import UserAdminRepository
from ent.features.users.schemas.requests import (
    CustomRoleCreate,
    CustomRoleUpdate,
    RoleAssignment,
    UserUpdate,
)
from ent.features.users.schemas.responses import (
    ClinicMembershipList,
    ClinicMembershipRead,
    PermissionRead,
    RoleRead,
    UserRead,
)


class UserAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserAdminRepository(session)

    async def list_users(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams | None,
        search: str | None = None,
    ) -> PageSchema[UserRead]:
        result = await self._repo.list_members(
            clinic_id=user.clinic_id,
            page=page,
            search=search,
        )
        items: list[UserRead] = []
        for row in result.items:
            codes = await self._repo.active_role_codes(
                clinic_id=user.clinic_id, user_id=row.id
            )
            items.append(_user_read(row, codes))
        return PageSchema(
            items=items,
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def get_user(self, *, user: CurrentUser, public_id: str) -> UserRead:
        row = await self._repo.get_member(clinic_id=user.clinic_id, public_id=public_id)
        if row is None:
            raise NotFoundError(resource="user", public_id=public_id)
        codes = await self._repo.active_role_codes(
            clinic_id=user.clinic_id, user_id=row.id
        )
        return _user_read(row, codes)

    async def update_user(
        self,
        *,
        actor: CurrentUser,
        public_id: str,
        body: UserUpdate,
    ) -> UserRead:
        row = await self._repo.get_member(
            clinic_id=actor.clinic_id, public_id=public_id
        )
        if row is None:
            raise NotFoundError(resource="user", public_id=public_id)
        data = body.model_dump(exclude_unset=True)
        if data.get("is_active") is False and row.id == actor.user_id:
            raise ValidationError(reason="cannot_deactivate_self")
        for field, value in data.items():
            setattr(row, field, value)
        row.updated_by_id = actor.user_id
        await self._session.flush()
        return await self.get_user(user=actor, public_id=public_id)

    async def assign_role(
        self,
        *,
        actor: CurrentUser,
        public_id: str,
        body: RoleAssignment,
    ) -> UserRead:
        member = await self._repo.get_member(
            clinic_id=actor.clinic_id, public_id=public_id
        )
        if member is None:
            raise NotFoundError(resource="user", public_id=public_id)
        role = await self._repo.get_role(
            clinic_id=actor.clinic_id, public_id=body.role_public_id
        )
        if role is None:
            raise NotFoundError(resource="role", public_id=body.role_public_id)
        site_id = await self._site_id(actor.clinic_id, body.site_public_id)
        existing = await self._repo.membership(
            clinic_id=actor.clinic_id, user_id=member.id, role_id=role.id
        )
        today = date.today()
        if existing is None:
            self._session.add(
                UserClinicRole(
                    public_id=new_ulid(),
                    clinic_id=actor.clinic_id,
                    user_id=member.id,
                    role_id=role.id,
                    site_id=site_id,
                    starts_on=today,
                    created_by_id=actor.user_id,
                    updated_by_id=actor.user_id,
                ),
            )
        else:
            existing.ends_on = None
            existing.site_id = site_id
            existing.updated_by_id = actor.user_id
        await self._session.flush()
        return await self.get_user(user=actor, public_id=public_id)

    async def revoke_role(
        self,
        *,
        actor: CurrentUser,
        public_id: str,
        role_public_id: str,
    ) -> UserRead:
        member = await self._repo.get_member(
            clinic_id=actor.clinic_id, public_id=public_id
        )
        if member is None:
            raise NotFoundError(resource="user", public_id=public_id)
        role = await self._repo.get_role(
            clinic_id=actor.clinic_id, public_id=role_public_id
        )
        if role is None:
            raise NotFoundError(resource="role", public_id=role_public_id)
        existing = await self._repo.membership(
            clinic_id=actor.clinic_id, user_id=member.id, role_id=role.id
        )
        if existing is None or (
            existing.ends_on is not None and existing.ends_on < date.today()
        ):
            raise NotFoundError(resource="user_clinic_role", public_id=role_public_id)
        existing.ends_on = date.today() - timedelta(days=1)
        existing.updated_by_id = actor.user_id
        await self._session.flush()
        codes = await self._repo.active_role_codes(
            clinic_id=actor.clinic_id, user_id=member.id
        )
        return _user_read(member, codes)

    async def list_roles(self, *, user: CurrentUser) -> list[RoleRead]:
        roles = await self._repo.list_roles(user.clinic_id)
        result: list[RoleRead] = []
        for role in roles:
            codes = await self._repo.permission_codes_for_role(role.id)
            result.append(_role_read(role, codes))
        return result

    async def list_permissions(self) -> list[PermissionRead]:
        rows = await self._repo.list_permissions()
        return [
            PermissionRead(code=row.code, group_code=row.group_code) for row in rows
        ]

    async def create_role(
        self, *, actor: CurrentUser, body: CustomRoleCreate
    ) -> RoleRead:
        if await self._repo.get_role_by_code(clinic_id=actor.clinic_id, code=body.code):
            raise ConflictError(reason="role_code_taken", code=body.code)
        permissions = await self._require_permissions(body.permission_codes)
        role = Role(
            public_id=new_ulid(),
            clinic_id=actor.clinic_id,
            code=body.code,
            name_key=body.name_key,
            is_system=False,
            created_by_id=actor.user_id,
            updated_by_id=actor.user_id,
        )
        self._session.add(role)
        await self._session.flush()
        await self._repo.replace_role_permissions(
            role_id=role.id,
            permission_ids=[row.id for row in permissions],
        )
        codes = await self._repo.permission_codes_for_role(role.id)
        return _role_read(role, codes)

    async def update_role(
        self,
        *,
        actor: CurrentUser,
        public_id: str,
        body: CustomRoleUpdate,
    ) -> RoleRead:
        role = await self._repo.get_role(clinic_id=actor.clinic_id, public_id=public_id)
        if role is None:
            raise NotFoundError(resource="role", public_id=public_id)
        if role.is_system:
            raise ConflictError(reason="system_role_locked", publicId=public_id)
        data = body.model_dump(exclude_unset=True)
        if "name_key" in data and data["name_key"] is not None:
            role.name_key = data["name_key"]
        if data.get("permission_codes") is not None:
            permissions = await self._require_permissions(data["permission_codes"])
            await self._repo.replace_role_permissions(
                role_id=role.id,
                permission_ids=[row.id for row in permissions],
            )
        role.updated_by_id = actor.user_id
        await self._session.flush()
        codes = await self._repo.permission_codes_for_role(role.id)
        return _role_read(role, codes)

    async def list_clinics(self, *, user: CurrentUser) -> ClinicMembershipList:
        rows = await self._repo.clinics_for_user(user.user_id)
        grouped: dict[str, ClinicMembershipRead] = {}
        for clinic, code in rows:
            item = grouped.get(clinic.public_id)
            if item is None:
                grouped[clinic.public_id] = ClinicMembershipRead(
                    clinic_public_id=clinic.public_id,
                    clinic_name=clinic.name,
                    role_codes=[code],
                )
            else:
                item.role_codes.append(code)
        return ClinicMembershipList(items=list(grouped.values()))

    async def _site_id(self, clinic_id: int, public_id: str | None) -> int | None:
        if public_id is None:
            return None
        site = await SiteRepository(
            self._session, clinic_id=clinic_id
        ).get_by_public_id(public_id)
        if site is None:
            raise NotFoundError(resource="site", public_id=public_id)
        return site.id

    async def _require_permissions(self, codes: list[str]) -> list[Permission]:
        found = await self._repo.permissions_by_codes(codes)
        found_codes = {row.code for row in found}
        missing = [code for code in codes if code not in found_codes]
        if missing:
            raise ValidationError(reason="unknown_permission", codes=missing)
        return found


def _user_read(row: User, role_codes: list[str]) -> UserRead:
    return UserRead(
        public_id=row.public_id,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        title=row.title,
        specialty=row.specialty,
        license_number=row.license_number,
        preferred_locale=row.preferred_locale,
        timezone=row.timezone,
        is_active=row.is_active,
        mfa_enabled=row.mfa_enabled,
        role_codes=role_codes,
    )


def _role_read(role: Role, codes: list[str]) -> RoleRead:
    return RoleRead(
        public_id=role.public_id,
        code=role.code,
        name_key=role.name_key,
        is_system=role.is_system,
        permission_codes=codes,
    )
