"""P3-06: a tube creates a device, recalls, and a card flag."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.otology.models import EarDevice
from ent.features.recalls.models import Recall
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("PROC.OTOSCOPY", "procedure", "Otoscopy"),
    ("PROC.OTOMICROSCOPY", "procedure", "Otomicroscopy"),
    ("PROC.VENTILATION_TUBE", "procedure", "Ventilation tube"),
    ("PROC.EAR_WICK", "procedure", "Ear wick"),
    ("PROC.CAVITY_CLEANING", "procedure", "Cavity cleaning"),
    ("ANAT.EAR.CANAL", "anatomy", "Canal"),
    ("ANAT.TM.PF", "anatomy", "Pars flaccida"),
    ("FIND.CANAL.NORMAL", "finding", "Normal canal"),
    ("FIND.TM.NORMAL", "finding", "Normal membrane"),
    ("FIND.TM.CHOLESTEATOMA", "finding", "Cholesteatoma"),
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tube_insertion_creates_device_recalls_and_flag() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            other = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["other_clinic_public_id"]
                    )
                )
            ).scalar_one()
            other_role = await ensure_role(
                session,
                clinic=other,
                code="clinic_admin",
                name_key="role.clinic_admin",
            )
            other_admin = await ensure_user_with_role(
                session,
                clinic=other,
                role=other_role,
                email=f"otology-other+{suffix}@test.entshifa.local",
                first_name="Other",
                last_name="Clinic",
                password=fixtures["password"],
            )
            await seed_terminology(session)
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
        for code, kind, display in _CATALOG:
            await _ensure_concept(
                client, headers, code=code, kind=kind, display=display
            )
        patient = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Ear",
                "lastName": f"Tube{suffix}",
                "birthDate": "1990-01-02",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        created = await client.post(
            "/api/v1/otology-exams",
            headers=headers,
            json=_tube(patient_id),
        )
        assert created.status_code == 201, created.text
        body = created.json()
        exam_id = body["publicId"]
        assert body["procedureCode"] == "PROC.VENTILATION_TUBE"
        assert len(body["devices"]) == 1
        device = body["devices"][0]
        assert device["deviceType"] == "ventilation_tube"
        assert device["status"] == "in_place"
        assert device["laterality"] == "right"
        assert device["nextCheckDue"] == "2026-06-23"

        chart = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
        assert chart.status_code == 200, chart.text
        flags = [
            row
            for row in chart.json()["flags"]
            if row["flagCode"] == "ventilation_tube" and row["endedOn"] is None
        ]
        assert len(flags) == 1
        assert flags[0]["laterality"] == "right"

        wick = await client.post(
            "/api/v1/otology-exams",
            headers=headers,
            json=_wick(patient_id),
        )
        assert wick.status_code == 201, wick.text
        assert wick.json()["procedure"]["removalDueDate"] == "2026-06-05"

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_admin.email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200, other_login.text
        hidden = await client.get(
            f"/api/v1/otology-exams/{exam_id}",
            headers={"Authorization": f"Bearer {other_login.json()['accessToken']}"},
        )
        assert hidden.status_code == 404, hidden.text
        assert hidden.json()["code"] == "otology.not_found"

        signed = await client.post(
            f"/api/v1/procedures/{body['procedureId']}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        locked = await client.put(
            f"/api/v1/otology-exams/{exam_id}",
            headers=headers,
            json={**_tube(patient_id), "version": body["version"]},
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "procedure.already_signed"

    async with factory() as session:
        device_count = (
            await session.execute(
                select(func.count())
                .select_from(EarDevice)
                .where(
                    EarDevice.public_id == device["publicId"],
                    EarDevice.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        stored = (
            await session.execute(
                select(EarDevice).where(EarDevice.public_id == device["publicId"])
            )
        ).scalar_one()
        recall_count = (
            await session.execute(
                select(func.count())
                .select_from(Recall)
                .where(
                    Recall.source_type == "procedure",
                    Recall.source_id == stored.inserted_procedure_id,
                    Recall.reason_key.in_(
                        ("otology_tube_patency", "otology_tube_check")
                    ),
                    Recall.status == "pending",
                    Recall.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        assert int(device_count) == 1
        assert int(recall_count) == 2


def _tube(patient_id: str) -> dict[str, object]:
    return {
        "patientPublicId": patient_id,
        "performedAt": "2026-06-02T09:15:00",
        "laterality": "right",
        "method": "microscopy",
        "forkFrequencyHz": 512,
        "weber": "lateralizes_right",
        "rinneRight": "negative",
        "mobilityRight": "reduced",
        "structures": [
            {
                "bodySiteCode": "ANAT.TM.PF",
                "laterality": "right",
                "status": "abnormal",
                "findingCode": "FIND.TM.CHOLESTEATOMA",
                "mapRegionCode": "tm.pars-flaccida",
            }
        ],
        "procedure": {
            "subtype": "tube_insertion",
            "tubeModel": "shepard",
            "effusion": "serous",
        },
    }


def _wick(patient_id: str) -> dict[str, object]:
    return {
        "patientPublicId": patient_id,
        "performedAt": "2026-06-02T10:00:00",
        "laterality": "left",
        "method": "otoscopy",
        "procedure": {"subtype": "wick", "wickType": "pope"},
    }


async def _ensure_concept(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    code: str,
    kind: str,
    display: str,
) -> None:
    found = await client.get(
        "/api/v1/terminology/concepts/search",
        headers=headers,
        params={"q": code, "limit": "20"},
    )
    assert found.status_code == 200, found.text
    if any(item["code"] == code for item in found.json()["items"]):
        return
    created = await client.post(
        "/api/v1/terminology/admin/concepts",
        headers=headers,
        json={"code": code, "kind": kind, "locale": "en", "display": display},
    )
    if created.status_code == 409:
        return
    assert created.status_code == 201, created.text
