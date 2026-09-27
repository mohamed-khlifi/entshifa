"""Seed identity rows for auth integration tests."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.seeds.identity import (
    LOCAL_DEV_PASSWORD,
    clinic_public_id_by_slug,
    clinic_public_id_for_user_login,
    ensure_clinic,
    ensure_role,
    ensure_user_with_role,
    load_clinic_by_slug,
)


async def seed_auth_fixtures(session: AsyncSession) -> dict[str, str]:
    suffix = new_ulid()[:8].lower()
    clinic_slug = f"test-{suffix}"
    other_clinic_slug = f"other-{suffix}"
    await ensure_clinic(
        session,
        slug=clinic_slug,
        name="Test Clinic",
        default_locale="en",
    )
    await ensure_clinic(
        session,
        slug=other_clinic_slug,
        name="Other Clinic",
        default_locale="en",
    )
    clinic = await load_clinic_by_slug(session, clinic_slug)
    role = await ensure_role(
        session,
        clinic=clinic,
        code="doctor",
        name_key="role.doctor",
    )
    user_email = f"doctor+{suffix}@test.entshifa.local"
    user = await ensure_user_with_role(
        session,
        clinic=clinic,
        role=role,
        email=user_email,
        first_name="Test",
        last_name="Doctor",
        password=LOCAL_DEV_PASSWORD,
    )

    return {
        "email": user.email,
        "password": LOCAL_DEV_PASSWORD,
        "clinic_public_id": await clinic_public_id_for_user_login(
            session,
            email=user_email,
        ),
        "other_clinic_public_id": await clinic_public_id_by_slug(
            session,
            other_clinic_slug,
        ),
        "user_public_id": user.public_id,
    }
