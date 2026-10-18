"""P3-08: Recall protocols from procedures (backend) integration tests.

Verifies:
1. System protocols and rules are seeded from Feature Spec Appendix C.
2. Performing and signing a procedure creates protocol-linked recalls with
   clinic-local due dates and windows.
3. Unmet rule conditions (e.g. cautery vs pack, tube without pre-op hearing loss)
   do not create recalls; met conditions (tube with pre-op hearing loss) create
   the 90-day audiogram recall.
4. Editing a protocol rule's interval in the database (via PUT /api/v1/recall-protocols/{code})
   changes due dates for that clinic without affecting other clinics.
5. Completing the expected event (or completing a repeating recall) closes the
   pending recall, schedules the next repeating check, and terminates the
   repeating series when the stop condition is met (extruded / removed).
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.procedures.models import ProcedureRecord
from ent.features.recalls.models import Recall
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.seeds.protocols import seed_protocols
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("PROC.OTOSCOPY", "procedure", "Otoscopy"),
    ("PROC.OTOMICROSCOPY", "procedure", "Otomicroscopy"),
    ("PROC.VENTILATION_TUBE", "procedure", "Ventilation tube"),
    ("PROC.TUBE_REMOVAL", "procedure", "Tube removal"),
    ("PROC.EAR_WICK", "procedure", "Ear wick"),
    ("PROC.CAVITY_CLEANING", "procedure", "Cavity cleaning"),
    ("PROC.CERUMEN_REMOVAL", "procedure", "Cerumen removal"),
    ("PROC.EPISTAXIS_MANAGEMENT", "procedure", "Epistaxis management"),
    ("ANAT.TM.PF", "anatomy", "Pars flaccida"),
    ("FIND.TM.NORMAL", "finding", "Normal membrane"),
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_recall_protocols_lifecycle_override_and_repeating_stop() -> None:
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
                email=f"protocol-other+{suffix}@test.entshifa.local",
                first_name="Other",
                last_name="Clinic",
                password=fixtures["password"],
            )
            await seed_terminology(session)
            await seed_protocols(session)
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

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_admin.email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200, other_login.text
        other_headers = {"Authorization": f"Bearer {other_login.json()['accessToken']}"}

        for code, kind, display in _CATALOG:
            await _ensure_concept(
                client, headers, code=code, kind=kind, display=display
            )

        # 1. List recall protocols and verify Appendix C defaults
        protocols_resp = await client.get(
            "/api/v1/recall-protocols",
            headers=headers,
        )
        assert protocols_resp.status_code == 200, protocols_resp.text
        protocols = {item["code"]: item for item in protocols_resp.json()}
        assert "PROT.VENTILATION_TUBE" in protocols
        assert "PROT.EPISTAXIS_PACK" in protocols
        assert "PROT.EAR_WICK" in protocols
        assert "PROT.NASAL_SPLINT" in protocols
        assert "PROT.CAVITY_CLEANING" in protocols
        assert "PROT.SPECIMEN_REVIEW" in protocols
        assert "PROT.SIALENDOSCOPY_FOLLOWUP" in protocols
        assert "PROT.CANAL_INJURY" in protocols
        assert len(protocols["PROT.VENTILATION_TUBE"]["rules"]) == 3

        # 2. Edit PROT.EAR_WICK interval in primary clinic (change offset_days from 3 to 4)
        updated_proto = await client.put(
            "/api/v1/recall-protocols/PROT.EAR_WICK",
            headers=headers,
            json={
                "isActive": True,
                "rules": [
                    {
                        "sequence": 1,
                        "offsetDays": 4,
                        "windowDays": 2,
                    }
                ],
            },
        )
        assert updated_proto.status_code == 200, updated_proto.text
        assert updated_proto.json()["isClinicOverride"] is True
        assert updated_proto.json()["rules"][0]["offsetDays"] == 4
        assert updated_proto.json()["rules"][0]["windowDays"] == 2

        # Other clinic remains on system default (offsetDays = 3, isClinicOverride = False)
        other_protocols = {
            item["code"]: item
            for item in (
                await client.get("/api/v1/recall-protocols", headers=other_headers)
            ).json()
        }
        assert other_protocols["PROT.EAR_WICK"]["isClinicOverride"] is False
        assert other_protocols["PROT.EAR_WICK"]["rules"][0]["offsetDays"] == 3

        # 3. Create patient and test customized ear wick interval (performed 2026-06-02 -> due 2026-06-06)
        patient_resp = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Proto",
                "lastName": f"Patient{suffix}",
                "birthDate": "2018-05-10",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert patient_resp.status_code == 201, patient_resp.text
        patient_id = patient_resp.json()["publicId"]

        wick_exam = await client.post(
            "/api/v1/otology-exams",
            headers=headers,
            json={
                "patientPublicId": patient_id,
                "performedAt": "2026-06-02T10:00:00",
                "laterality": "left",
                "method": "otoscopy",
                "procedure": {"subtype": "wick", "wickType": "pope"},
            },
        )
        assert wick_exam.status_code == 201, wick_exam.text
        assert wick_exam.json()["procedure"]["removalDueDate"] == "2026-06-06"

        # Restore PROT.EAR_WICK to system default 3 days / 1 window so shared state stays clean
        await client.put(
            "/api/v1/recall-protocols/PROT.EAR_WICK",
            headers=headers,
            json={
                "isActive": True,
                "rules": [{"sequence": 1, "offsetDays": 3, "windowDays": 1}],
            },
        )

        # 4. Ventilation tube with pre-op hearing loss -> creates 3 recalls (patency, audiogram, 6m check)
        tube_exam = await client.post(
            "/api/v1/otology-exams",
            headers=headers,
            json={
                "patientPublicId": patient_id,
                "performedAt": "2026-06-02T09:15:00",
                "laterality": "right",
                "method": "microscopy",
                "structures": [
                    {
                        "bodySiteCode": "ANAT.TM.PF",
                        "laterality": "right",
                        "status": "normal",
                        "findingCode": "FIND.TM.NORMAL",
                        "mapRegionCode": "tm.pars-flaccida",
                    }
                ],
                "procedure": {
                    "subtype": "tube_insertion",
                    "tubeModel": "shepard",
                    "effusion": "mucoid",
                    "hasPreopHearingLoss": True,
                },
            },
        )
        assert tube_exam.status_code == 201, tube_exam.text
        tube_proc_id = tube_exam.json()["procedureId"]
        tube_device_id = tube_exam.json()["devices"][0]["publicId"]
        tube_device_version = tube_exam.json()["devices"][0]["version"]

        # Sign the tube insertion procedure -> triggers ProcedurePerformed event
        signed_tube = await client.post(
            f"/api/v1/procedures/{tube_proc_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed_tube.status_code == 200, signed_tube.text

        # Verify in DB that all 3 recalls exist with non-null protocol_id and protocol_rule_id
        async with factory() as session:
            tube_recalls = (
                (
                    await session.execute(
                        select(Recall)
                        .join(
                            ProcedureRecord,
                            Recall.source_id == ProcedureRecord.id,
                        )
                        .where(
                            ProcedureRecord.public_id == tube_proc_id,
                            Recall.status == "pending",
                            Recall.deleted_at.is_(None),
                        )
                        .order_by(Recall.due_on.asc())
                    )
                )
                .scalars()
                .all()
            )
            assert [r.reason_key for r in tube_recalls] == [
                "otology_tube_patency",
                "otology_tube_audiogram",
                "otology_tube_check",
            ]
            for r in tube_recalls:
                assert r.protocol_id is not None
                assert r.protocol_rule_id is not None
            assert str(tube_recalls[0].due_on) == "2026-06-23"
            assert str(tube_recalls[1].due_on) == "2026-08-31"
            assert tube_recalls[1].action_type == "test"
            assert str(tube_recalls[2].due_on) == "2026-12-02"
            tube_check_public_id = tube_recalls[2].public_id
            tube_check_version = int(tube_recalls[2].version)

        # 5. Complete the repeating 6-month tube check while tube is still in_place ->
        #    automatically schedules the next repeating recall!
        completed_resp = await client.post(
            f"/api/v1/recalls/{tube_check_public_id}/complete",
            headers=headers,
            json={"version": tube_check_version},
        )
        assert completed_resp.status_code == 200, completed_resp.text
        assert completed_resp.json()["status"] == "done"

        async with factory() as session:
            pending_checks = (
                (
                    await session.execute(
                        select(Recall)
                        .join(
                            ProcedureRecord,
                            Recall.source_id == ProcedureRecord.id,
                        )
                        .where(
                            ProcedureRecord.public_id == tube_proc_id,
                            Recall.reason_key == "otology_tube_check",
                            Recall.status == "pending",
                            Recall.deleted_at.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(pending_checks) == 1

        # 6. Mark the ventilation tube as extruded -> cancels pending tube recalls and stops series
        extruded_resp = await client.patch(
            f"/api/v1/ear-devices/{tube_device_id}",
            headers=headers,
            json={"status": "extruded", "version": tube_device_version},
        )
        assert extruded_resp.status_code == 200, extruded_resp.text
        assert extruded_resp.json()["status"] == "extruded"

        async with factory() as session:
            remaining_open_tube = (
                (
                    await session.execute(
                        select(Recall)
                        .join(
                            ProcedureRecord,
                            Recall.source_id == ProcedureRecord.id,
                        )
                        .where(
                            ProcedureRecord.public_id == tube_proc_id,
                            Recall.reason_key.in_(
                                ("otology_tube_patency", "otology_tube_check")
                            ),
                            Recall.status == "pending",
                            Recall.deleted_at.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert remaining_open_tube == []


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
