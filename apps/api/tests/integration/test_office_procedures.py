"""P3-07: a pack and a biopsy record their dates and open a recall."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.procedures.models import ProcedureRecord
from ent.features.recalls.models import Recall
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("PROC.EPISTAXIS_MANAGEMENT", "procedure", "Epistaxis management"),
    ("PROC.ORAL_PHARYNGEAL_BIOPSY", "procedure", "Oral or pharyngeal biopsy"),
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pack_and_biopsy_record_dates_and_recalls() -> None:
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
                email=f"office-other+{suffix}@test.entshifa.local",
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
                "firstName": "Nose",
                "lastName": f"Pack{suffix}",
                "birthDate": "1984-04-04",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        created = await client.post(
            "/api/v1/office-procedures",
            headers=headers,
            json=_pack(patient_id),
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["procedure"]["code"] == "PROC.EPISTAXIS_MANAGEMENT"
        assert body["removalDueDate"] == "2026-06-04"
        assert body["resultDueDate"] is None
        assert body["detail"]["method"] == "anterior_pack"
        office_id = body["publicId"]
        procedure_id = body["procedureId"]

        biopsy = await client.post(
            "/api/v1/office-procedures",
            headers=headers,
            json=_biopsy(patient_id),
        )
        assert biopsy.status_code == 201, biopsy.text
        assert biopsy.json()["resultDueDate"] == "2026-06-09"
        assert biopsy.json()["removalDueDate"] is None
        biopsy_procedure_id = biopsy.json()["procedureId"]

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/office-procedures",
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["page"]["total"] == 2

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_admin.email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200, other_login.text
        hidden = await client.get(
            f"/api/v1/office-procedures/{office_id}",
            headers={"Authorization": f"Bearer {other_login.json()['accessToken']}"},
        )
        assert hidden.status_code == 404, hidden.text
        assert hidden.json()["code"] == "office_procedure.not_found"

        cautery = _pack(patient_id)
        detail = cautery["detail"]
        assert isinstance(detail, dict)
        detail["method"] = "silver_nitrate"
        detail["siteFound"] = True
        detail["bleedingSite"] = "little_area"
        detail.pop("packType")
        detail.pop("packRemovalDate")
        updated = await client.put(
            f"/api/v1/office-procedures/{office_id}",
            headers=headers,
            json={**cautery, "version": body["version"]},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["removalDueDate"] is None

        signed = await client.post(
            f"/api/v1/procedures/{procedure_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        locked = await client.put(
            f"/api/v1/office-procedures/{office_id}",
            headers=headers,
            json={**_pack(patient_id), "version": updated.json()["version"]},
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "procedure.already_signed"

    async with factory() as session:

        def _scoped(public_id: str, reason_key: str, status: str) -> object:
            return (
                select(func.count())
                .select_from(Recall)
                .join(ProcedureRecord, Recall.source_id == ProcedureRecord.id)
                .where(
                    ProcedureRecord.public_id == public_id,
                    Recall.reason_key == reason_key,
                    Recall.status == status,
                    Recall.deleted_at.is_(None),
                )
            )

        pack_recalls = (
            await session.execute(
                _scoped(procedure_id, "office_pack_removal", "pending")
            )
        ).scalar_one()
        cancelled = (
            await session.execute(
                _scoped(procedure_id, "office_pack_removal", "cancelled")
            )
        ).scalar_one()
        specimen = (
            await session.execute(
                _scoped(biopsy_procedure_id, "office_specimen_review", "pending")
            )
        ).scalar_one()
        assert int(pack_recalls) == 0
        assert int(cancelled) >= 1
        assert int(specimen) == 1


def _pack(patient_id: str) -> dict[str, object]:
    return {
        "patientPublicId": patient_id,
        "performedAt": "2026-06-02T09:15:00",
        "laterality": "right",
        "anesthesia": "topical_spray",
        "detail": {
            "subtype": "epistaxis_management",
            "siteFound": False,
            "method": "anterior_pack",
            "packType": "merocel",
            "packRemovalDate": "2026-06-04",
            "systolicBp": 150,
            "diastolicBp": 92,
            "anticoagulantStatus": "yes",
            "adviceText": "Pinch and lean forward",
            "adviceLocale": "en",
        },
    }


def _biopsy(patient_id: str) -> dict[str, object]:
    return {
        "patientPublicId": patient_id,
        "performedAt": "2026-06-02T10:00:00",
        "laterality": "left",
        "anesthesia": "local_infiltration",
        "detail": {
            "subtype": "oral_pharyngeal_biopsy",
            "site": "tonsil",
            "technique": "punch",
            "laboratoryText": "City lab",
            "laboratoryLocale": "en",
            "resultDueDate": "2026-06-09",
        },
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
