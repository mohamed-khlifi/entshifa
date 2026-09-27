"""Seed helpers for clinic admin API tests."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.seeds.identity import (
    LOCAL_DEV_PASSWORD,
    clinic_public_id_by_slug,
    ensure_all_permissions,
    ensure_clinic,
    ensure_role,
    ensure_site,
    ensure_user_with_role,
)


async def seed_clinic_admin_fixtures(session: AsyncSession) -> dict[str, str]:
    await ensure_all_permissions(session)
    suffix = new_ulid()[:8].lower()
    clinic_slug = f"admin-{suffix}"
    other_clinic_slug = f"other-admin-{suffix}"
    clinic = await ensure_clinic(
        session,
        slug=clinic_slug,
        name="Admin Test Clinic",
        default_locale="en",
    )
    other = await ensure_clinic(
        session,
        slug=other_clinic_slug,
        name="Other Admin Clinic",
        default_locale="en",
    )
    await ensure_site(session, clinic=clinic, name="Primary", is_primary=True)
    other_site = await ensure_site(
        session, clinic=other, name="Other Primary", is_primary=True
    )

    admin_role = await ensure_role(
        session,
        clinic=clinic,
        code="clinic_admin",
        name_key="role.clinic_admin",
    )
    doctor_role = await ensure_role(
        session,
        clinic=clinic,
        code="doctor",
        name_key="role.doctor",
    )
    admin = await ensure_user_with_role(
        session,
        clinic=clinic,
        role=admin_role,
        email=f"admin+{suffix}@test.entshifa.local",
        first_name="Admin",
        last_name="User",
        password=LOCAL_DEV_PASSWORD,
    )
    doctor = await ensure_user_with_role(
        session,
        clinic=clinic,
        role=doctor_role,
        email=f"doctor+{suffix}@test.entshifa.local",
        first_name="Doc",
        last_name="Tor",
        password=LOCAL_DEV_PASSWORD,
    )

    return {
        "admin_email": admin.email,
        "doctor_email": doctor.email,
        "password": LOCAL_DEV_PASSWORD,
        "clinic_public_id": await clinic_public_id_by_slug(session, clinic_slug),
        "other_clinic_public_id": await clinic_public_id_by_slug(
            session,
            other_clinic_slug,
        ),
        "other_site_public_id": other_site.public_id,
    }
