"""Seed identity rows for auth integration tests."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.seeds.identity import (
    LOCAL_DEV_PASSWORD,
    ensure_clinic,
    ensure_role,
    ensure_user_with_role,
)


async def seed_auth_fixtures(session: AsyncSession) -> dict[str, str]:
    suffix = new_ulid()[:8].lower()
    clinic = await ensure_clinic(
        session,
        slug=f"test-{suffix}",
        name="Test Clinic",
        default_locale="en",
    )
    role = await ensure_role(
        session,
        clinic=clinic,
        code="doctor",
        name_key="role.doctor",
    )
    user = await ensure_user_with_role(
        session,
        clinic=clinic,
        role=role,
        email=f"doctor+{suffix}@test.entshifa.local",
        first_name="Test",
        last_name="Doctor",
        password=LOCAL_DEV_PASSWORD,
    )

    other = await ensure_clinic(
        session,
        slug=f"other-{suffix}",
        name="Other Clinic",
        default_locale="en",
    )

    return {
        "email": user.email,
        "password": LOCAL_DEV_PASSWORD,
        "clinic_public_id": clinic.public_id,
        "other_clinic_public_id": other.public_id,
        "user_public_id": user.public_id,
    }
