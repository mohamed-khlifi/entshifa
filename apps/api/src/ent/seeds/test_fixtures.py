"""Deterministic fixtures for the test suite (architecture §28 seed_test)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.engines.patients.name_normalize import build_name_normalized
from ent.features.patients.models import Patient
from ent.seeds.identity import (
    LOCAL_DEV_PASSWORD,
    ensure_clinic,
    ensure_role,
    ensure_site,
    ensure_user_with_role,
    load_clinic_by_slug,
)
from ent.seeds.system import seed_system

TEST_CLINIC_SLUG = "test-entshifa"
TEST_OTHER_CLINIC_SLUG = "test-entshifa-b"
TEST_ADMIN_EMAIL = "admin@test.entshifa.local"
TEST_PATIENT_MRN = "TESTMRN0001"
TEST_PATIENT_LAST_NAME = "Fixture"


@dataclass(frozen=True, slots=True)
class TestSeedReport:
    clinic_slug: str
    other_clinic_slug: str
    admin_email: str
    password: str
    patient_mrn: str


async def seed_test(session: AsyncSession) -> TestSeedReport:
    """System data plus two fixed clinics, an admin, and one patient."""

    await seed_system(session)
    clinic = await ensure_clinic(
        session,
        slug=TEST_CLINIC_SLUG,
        name="Test Fixture Clinic",
        default_locale="en",
    )
    other = await ensure_clinic(
        session,
        slug=TEST_OTHER_CLINIC_SLUG,
        name="Test Fixture Clinic B",
        default_locale="en",
    )
    clinic = await load_clinic_by_slug(session, TEST_CLINIC_SLUG)
    other = await load_clinic_by_slug(session, TEST_OTHER_CLINIC_SLUG)
    await ensure_site(session, clinic=clinic, name="Fixture primary", is_primary=True)
    await ensure_site(session, clinic=other, name="Fixture other", is_primary=True)
    role = await ensure_role(
        session,
        clinic=clinic,
        code="clinic_admin",
        name_key="role.clinic_admin",
    )
    await ensure_user_with_role(
        session,
        clinic=clinic,
        role=role,
        email=TEST_ADMIN_EMAIL,
        first_name="Fixture",
        last_name="Admin",
        password=LOCAL_DEV_PASSWORD,
    )
    existing = (
        await session.execute(
            select(Patient.id).where(
                Patient.clinic_id == clinic.id,
                Patient.mrn == TEST_PATIENT_MRN,
                Patient.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            Patient(
                public_id=new_ulid(),
                clinic_id=clinic.id,
                mrn=TEST_PATIENT_MRN,
                first_name="Fixture",
                last_name=TEST_PATIENT_LAST_NAME,
                name_normalized=build_name_normalized(
                    first_name="Fixture",
                    last_name=TEST_PATIENT_LAST_NAME,
                ),
                birth_date=date(1980, 1, 15),
                sex="female",
                preferred_locale="en",
            ),
        )
        await session.flush()
    return TestSeedReport(
        clinic_slug=TEST_CLINIC_SLUG,
        other_clinic_slug=TEST_OTHER_CLINIC_SLUG,
        admin_email=TEST_ADMIN_EMAIL,
        password=LOCAL_DEV_PASSWORD,
        patient_mrn=TEST_PATIENT_MRN,
    )
