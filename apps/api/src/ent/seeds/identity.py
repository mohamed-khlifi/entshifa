"""Shared helpers for identity / auth seed data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.passwords import hash_password
from ent.core.security.permissions import Permission, permission_codes_for_role
from ent.core.utils.ids import new_ulid
from ent.features.auth.models import Permission as PermissionModel
from ent.features.auth.models import Role, RolePermission
from ent.features.auth.repository import AuthRepository
from ent.features.clinics.models import Clinic, Site
from ent.features.users.models import User, UserClinicRole

LOCAL_DEV_PASSWORD = "LocalDevSeed1!"


@dataclass(frozen=True, slots=True)
class SeededUser:
    email: str
    role_code: str
    public_id: str


async def ensure_all_permissions(session: AsyncSession) -> int:
    repo = AuthRepository(session)
    created = 0
    for perm in Permission:
        existing = (
            await session.execute(
                select(PermissionModel.id).where(PermissionModel.code == perm.value),
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        await repo.ensure_permission_row(perm.value, perm.value.split(".", maxsplit=1)[0])
        created += 1
    return created


async def ensure_clinic(
    session: AsyncSession,
    *,
    slug: str,
    name: str,
    default_locale: str = "fr",
) -> Clinic:
    existing = (
        await session.execute(
            select(Clinic).where(Clinic.slug == slug, Clinic.deleted_at.is_(None)),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    clinic = Clinic(
        public_id=new_ulid(),
        name=name,
        slug=slug,
        default_locale=default_locale,
        supported_locales=["fr", "en"],
        timezone="Europe/Paris",
        country_code="FR",
        currency="EUR",
        address_line1="12 rue de la Santé",
        city="Paris",
        postal_code="75014",
        phone="+33100000000",
        email=f"contact@{slug}.local",
        settings={"pta_formula": "iso7029"},
    )
    session.add(clinic)
    await session.flush()
    return clinic


async def ensure_site(
    session: AsyncSession,
    *,
    clinic: Clinic,
    name: str,
    is_primary: bool,
) -> Site:
    stmt = select(Site).where(
        Site.clinic_id == clinic.id,
        Site.name == name,
        Site.deleted_at.is_(None),
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing

    site = Site(
        public_id=new_ulid(),
        clinic_id=clinic.id,
        name=name,
        address_line1=clinic.address_line1,
        city=clinic.city,
        postal_code=clinic.postal_code,
        phone=clinic.phone,
        is_primary=is_primary,
    )
    session.add(site)
    await session.flush()
    return site


async def ensure_role(
    session: AsyncSession,
    *,
    clinic: Clinic,
    code: str,
    name_key: str,
) -> Role:
    stmt = select(Role).where(
        Role.clinic_id == clinic.id,
        Role.code == code,
        Role.deleted_at.is_(None),
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        await _ensure_role_permissions(session, existing)
        return existing

    role = Role(
        public_id=new_ulid(),
        clinic_id=clinic.id,
        code=code,
        name_key=name_key,
        is_system=True,
    )
    session.add(role)
    await session.flush()
    await _ensure_role_permissions(session, role)
    return role


async def _ensure_role_permissions(session: AsyncSession, role: Role) -> None:
    repo = AuthRepository(session)
    codes = permission_codes_for_role(role.code)
    for code in codes:
        perm = await repo.ensure_permission_row(
            code,
            code.split(".", maxsplit=1)[0],
        )
        link_exists = (
            await session.execute(
                select(RolePermission.id).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id,
                ),
            )
        ).scalar_one_or_none()
        if link_exists is not None:
            continue
        session.add(
            RolePermission(
                public_id=new_ulid(),
                role_id=role.id,
                permission_id=perm.id,
            ),
        )
    await session.flush()


async def ensure_user_with_role(
    session: AsyncSession,
    *,
    clinic: Clinic,
    role: Role,
    email: str,
    first_name: str,
    last_name: str,
    password: str = LOCAL_DEV_PASSWORD,
) -> SeededUser:
    stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
    existing = (await session.execute(stmt)).scalar_one_or_none()
    now = datetime.now(UTC).replace(tzinfo=None)

    if existing is None:
        user = User(
            public_id=new_ulid(),
            email=email,
            password_hash=hash_password(password),
            password_changed_at=now,
            first_name=first_name,
            last_name=last_name,
            preferred_locale="fr",
            timezone="Europe/Paris",
        )
        session.add(user)
        await session.flush()
    else:
        user = existing

    membership = (
        await session.execute(
            select(UserClinicRole.id).where(
                UserClinicRole.user_id == user.id,
                UserClinicRole.clinic_id == clinic.id,
                UserClinicRole.role_id == role.id,
                UserClinicRole.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if membership is None:
        session.add(
            UserClinicRole(
                public_id=new_ulid(),
                clinic_id=clinic.id,
                user_id=user.id,
                role_id=role.id,
                starts_on=date.today(),
            ),
        )
        await session.flush()

    return SeededUser(email=email, role_code=role.code, public_id=user.public_id)
