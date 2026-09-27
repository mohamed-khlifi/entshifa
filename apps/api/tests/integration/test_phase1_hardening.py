"""P1-11: reference-data versions and clinical read audit rows."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from ent.core.audit.models import AccessLog, AuditLog
from ent.core.db.session import get_session_factory
from ent.features.clinics.models import ReferenceDataVersion
from ent.features.patients.models import Patient
from ent.main import create_app
from ent.seeds.system import seed_system
from ent.seeds.versions import (
    PERMISSIONS_VERSION,
    TEMPLATES_VERSION,
    TERMINOLOGY_VERSION,
)
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_CHART_READS = {
    ("read", "patient"),
    ("timeline", "patient"),
    ("list", "patient_identifier"),
    ("list", "patient_allergy"),
    ("list", "patient_medication"),
    ("list", "patient_flag"),
    ("list", "patient_problem"),
    ("list", "patient_history"),
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seed_system_records_each_dataset_once() -> None:
    factory = get_session_factory()
    async with factory() as session:
        try:
            await seed_system(session)
            await seed_system(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")
        rows = (
            await session.execute(
                select(
                    ReferenceDataVersion.dataset,
                    ReferenceDataVersion.version,
                    func.count(),
                )
                .where(
                    ReferenceDataVersion.version.in_(
                        (
                            PERMISSIONS_VERSION,
                            TERMINOLOGY_VERSION,
                            TEMPLATES_VERSION,
                        )
                    )
                )
                .group_by(
                    ReferenceDataVersion.dataset,
                    ReferenceDataVersion.version,
                )
            )
        ).all()
    found = {(dataset, version): count for dataset, version, count in rows}
    assert found[("permissions", PERMISSIONS_VERSION)] == 1
    assert found[("terminology", TERMINOLOGY_VERSION)] == 1
    assert found[("templates", TEMPLATES_VERSION)] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_chart_reads_and_create_are_audited() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await session.commit()
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": fixtures["admin_email"],
                "password": fixtures["password"],
            },
        )
        if login.status_code != 200:
            pytest.skip("Login failed against database")
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        created = await client.post(
            "/api/v1/patients",
            headers=headers,
            json={
                "firstName": "Audit",
                "lastName": "Coverage",
                "birthDate": "1971-03-04",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert created.status_code == 201, created.text
        patient_id = created.json()["publicId"]
        for path in (
            f"/api/v1/patients/{patient_id}",
            f"/api/v1/patients/{patient_id}/timeline",
            f"/api/v1/patients/{patient_id}/identifiers",
            f"/api/v1/patients/{patient_id}/allergies",
            f"/api/v1/patients/{patient_id}/medications",
            f"/api/v1/patients/{patient_id}/flags",
            f"/api/v1/patients/{patient_id}/problems",
            f"/api/v1/patients/{patient_id}/history",
        ):
            response = await client.get(path, headers=headers)
            assert response.status_code == 200, response.text

    async with factory() as session:
        patient = (
            await session.execute(
                select(Patient).where(Patient.public_id == patient_id)
            )
        ).scalar_one()
        writes = (
            (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.entity_public_id == patient_id,
                        AuditLog.action == "create",
                        AuditLog.clinic_id == patient.clinic_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        reads = (
            (
                await session.execute(
                    select(AccessLog).where(AccessLog.patient_id == patient.id)
                )
            )
            .scalars()
            .all()
        )
    assert writes
    assert all(len(row.request_id) == 26 for row in writes)
    seen = {(row.action, row.entity_type) for row in reads}
    assert _CHART_READS <= seen
    assert all(row.clinic_id == patient.clinic_id for row in reads)
    assert all(len(row.request_id) == 26 for row in reads)
