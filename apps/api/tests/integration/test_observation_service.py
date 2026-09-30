"""P2-01 observation engine: bilateral rows, one-query diff, indexed cohort."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select, text
from sqlalchemy.engine import Connection

from ent.core.audit.models import AccessLog, AuditLog
from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.observations.models import Observation
from ent.features.observations.repository import ObservationRepository
from ent.features.patients.models import Patient
from ent.features.terminology.models import CodeSystem, Concept
from ent.main import create_app
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_observations_are_typed_sided_and_comparable() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    polyp_code = f"FIND.NOSE.POLYP.{suffix}"
    size_code = f"QUAL.SIZE.{suffix}"
    encounter_a = new_ulid()
    encounter_b = new_ulid()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await seed_terminology(session)
            system = (await session.execute(select(CodeSystem).limit(1))).scalar_one()
            session.add_all(
                [
                    Concept(
                        public_id=new_ulid(),
                        code_system_id=system.id,
                        code=polyp_code,
                        kind="finding",
                        sort_order=0,
                    ),
                    Concept(
                        public_id=new_ulid(),
                        code_system_id=system.id,
                        code=size_code,
                        kind="qualifier",
                        sort_order=0,
                    ),
                ]
            )
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
                "firstName": "Obs",
                "lastName": f"Engine{suffix}",
                "birthDate": "1982-02-02",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert created.status_code == 201, created.text
        patient_id = created.json()["publicId"]

        invalid = await client.post(
            f"/api/v1/observations/patient/{patient_id}/batch",
            headers=headers,
            json={
                "encounterPublicId": encounter_a,
                "observations": [
                    {
                        "conceptCode": "FIND.TM.PERFORATION",
                        "laterality": "right",
                        "status": "abnormal",
                        "valueType": "ordinal",
                        "ordinalValue": 3,
                        "valueText": "grade 3",
                        "effectiveAt": "2026-06-01T09:00:00",
                    }
                ],
            },
        )
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "observation.invalid_value_type"

        recorded = await client.post(
            f"/api/v1/observations/patient/{patient_id}/batch",
            headers=headers,
            json={
                "encounterPublicId": encounter_a,
                "observations": [
                    {
                        "conceptCode": "FIND.TM.PERFORATION",
                        "bodySiteCode": "ANAT.TM",
                        "mapRegionCode": "tm.pars-tensa.antero-inferior",
                        "laterality": "bilateral",
                        "status": "abnormal",
                        "valueType": "boolean",
                        "valueBoolean": True,
                        "effectiveAt": "2026-06-01T09:00:00",
                        "source": "clinician",
                        "confirmed": True,
                        "components": [
                            {
                                "conceptCode": size_code,
                                "valueType": "numeric",
                                "valueNumeric": "40",
                                "valueUnit": "%",
                            }
                        ],
                    },
                    {
                        "conceptCode": polyp_code,
                        "bodySiteCode": "ANAT.NASAL_CAVITY",
                        "laterality": "right",
                        "status": "abnormal",
                        "valueType": "ordinal",
                        "ordinalValue": 3,
                        "effectiveAt": "2026-06-01T09:00:00",
                        "source": "clinician",
                    },
                ],
            },
        )
        assert recorded.status_code == 201, recorded.text
        body = recorded.json()
        sides = {
            row["laterality"]
            for row in body
            if row["concept"]["code"] == "FIND.TM.PERFORATION"
        }
        assert sides == {"right", "left"}
        assert len(body) == 3
        for row in body:
            if row["concept"]["code"] == "FIND.TM.PERFORATION":
                assert len(row["components"]) == 1
                assert Decimal(str(row["components"][0]["valueNumeric"])) == Decimal(
                    "40"
                )
                assert row["confirmedByPublicId"]
        polyp = next(row for row in body if row["concept"]["code"] == polyp_code)
        assert polyp["ordinalValue"] == 3

        second = await client.post(
            f"/api/v1/observations/patient/{patient_id}/batch",
            headers=headers,
            json={
                "encounterPublicId": encounter_b,
                "observations": [
                    {
                        "conceptCode": polyp_code,
                        "bodySiteCode": "ANAT.NASAL_CAVITY",
                        "laterality": "right",
                        "status": "abnormal",
                        "valueType": "ordinal",
                        "ordinalValue": 1,
                        "effectiveAt": "2026-08-01T09:00:00",
                        "source": "clinician",
                    }
                ],
            },
        )
        assert second.status_code == 201, second.text

        diff = await client.get(
            f"/api/v1/observations/patient/{patient_id}/diff",
            headers=headers,
            params={"encounterA": encounter_a, "encounterB": encounter_b},
        )
        assert diff.status_code == 200, diff.text
        polyp_diff = next(
            row for row in diff.json() if row["concept"]["code"] == polyp_code
        )
        assert polyp_diff["laterality"] == "right"
        assert polyp_diff["visitA"]["ordinalValue"] == 3
        assert polyp_diff["visitB"]["ordinalValue"] == 1
        perforation_sides = {
            row["laterality"]
            for row in diff.json()
            if row["concept"]["code"] == "FIND.TM.PERFORATION"
        }
        assert perforation_sides == {"right", "left"}

        cohort = await client.get(
            "/api/v1/observations/cohort",
            headers=headers,
            params={
                "conceptCode": polyp_code,
                "ordinal": 3,
                "effectiveFrom": "2026-01-01T00:00:00",
                "effectiveTo": "2027-01-01T00:00:00",
            },
        )
        assert cohort.status_code == 200, cohort.text
        assert cohort.json()["page"]["total"] == 1
        assert cohort.json()["items"][0]["patientPublicId"] == patient_id
        absent = await client.get(
            "/api/v1/observations/cohort",
            headers=headers,
            params={
                "conceptCode": polyp_code,
                "ordinal": 2,
                "effectiveFrom": "2026-01-01T00:00:00",
                "effectiveTo": "2027-01-01T00:00:00",
            },
        )
        assert absent.json()["page"]["total"] == 0

        timeline = await client.get(
            f"/api/v1/observations/patient/{patient_id}/concept/{polyp_code}/timeline",
            headers=headers,
        )
        assert timeline.status_code == 200, timeline.text
        assert timeline.json()["page"]["total"] == 2

        foreign = await client.get(
            f"/api/v1/observations/encounter/{new_ulid()}",
            headers=headers,
        )
        assert foreign.status_code == 404

        snapshot = await client.post(
            f"/api/v1/observations/patient/{patient_id}/snapshots",
            headers=headers,
            json={
                "encounterPublicId": encounter_a,
                "mapId": "tympanic-membrane",
                "laterality": "right",
                "payload": {"region": "tm.pars-tensa.antero-inferior"},
            },
        )
        assert snapshot.status_code == 201, snapshot.text
        listed = await client.get(
            f"/api/v1/observations/patient/{patient_id}/snapshots",
            headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["page"]["total"] == 1

        updated = await client.patch(
            f"/api/v1/observations/{polyp['publicId']}",
            headers=headers,
            json={
                "version": polyp["version"],
                "status": "abnormal",
                "valueType": "ordinal",
                "ordinalValue": 4,
            },
        )
        assert updated.status_code == 200, updated.text
        conflict = await client.patch(
            f"/api/v1/observations/{polyp['publicId']}",
            headers=headers,
            json={
                "version": polyp["version"],
                "status": "abnormal",
                "valueType": "ordinal",
                "ordinalValue": 2,
            },
        )
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "observation.version_conflict"

        right_perf = next(
            row
            for row in body
            if row["concept"]["code"] == "FIND.TM.PERFORATION"
            and row["laterality"] == "right"
        )
        deleted = await client.delete(
            f"/api/v1/observations/{right_perf['publicId']}",
            headers=headers,
        )
        assert deleted.status_code == 204
        remaining = await client.get(
            f"/api/v1/observations/encounter/{encounter_a}",
            headers=headers,
        )
        assert remaining.status_code == 200, remaining.text
        assert right_perf["publicId"] not in {
            row["publicId"] for row in remaining.json()["items"]
        }

        other_patient = new_ulid()
        hidden = await client.get(
            f"/api/v1/observations/patient/{other_patient}/snapshots",
            headers=headers,
        )
        assert hidden.status_code == 404

    async with factory() as session:
        patient = (
            await session.execute(
                select(Patient).where(Patient.public_id == patient_id)
            )
        ).scalar_one()
        statements: list[str] = []

        def _capture(
            _conn: Connection,
            _cursor: object,
            statement: str,
            _parameters: object,
            _context: object,
            _executemany: bool,
        ) -> None:
            normalized = " ".join(statement.lower().split())
            if "group by" in normalized and "observation" in normalized:
                statements.append(normalized)

        bind = session.sync_session.get_bind()
        event.listen(bind, "before_cursor_execute", _capture)
        try:
            rows = await ObservationRepository(
                session, clinic_id=int(patient.clinic_id)
            ).diff_encounters_by_body_site(
                patient_id=int(patient.id),
                encounter_public_id_a=encounter_a,
                encounter_public_id_b=encounter_b,
            )
        finally:
            event.remove(bind, "before_cursor_execute", _capture)
        assert len(statements) == 1
        assert any(row.ordinal_a == 4 and row.ordinal_b == 1 for row in rows)

        explain = (
            (
                await session.execute(
                    text(
                        "EXPLAIN SELECT id FROM observation "
                        "WHERE clinic_id = :clinic_id AND concept_id = :concept_id "
                        "AND ordinal_value = :ordinal AND effective_at >= :start "
                        "AND effective_at < :end"
                    ),
                    {
                        "clinic_id": int(patient.clinic_id),
                        "concept_id": int(
                            (
                                await session.execute(
                                    select(Observation.concept_id).where(
                                        Observation.patient_id == patient.id,
                                        Observation.ordinal_value == 1,
                                    )
                                )
                            ).scalar_one()
                        ),
                        "ordinal": 3,
                        "start": datetime(2026, 1, 1),
                        "end": datetime(2027, 1, 1),
                    },
                )
            )
            .mappings()
            .one()
        )
        possible = str(explain["possible_keys"] or "")
        assert "ix_observation__cohort_ordinal" in possible

        actions = set(
            (
                await session.execute(
                    select(AccessLog.action, AccessLog.entity_type).where(
                        AccessLog.patient_id == patient.id,
                        AccessLog.entity_type.in_(
                            ("observation", "examination_snapshot")
                        ),
                    )
                )
            ).all()
        )
        assert ("timeline", "observation") in actions
        assert ("diff", "observation") in actions
        assert ("list", "examination_snapshot") in actions
        writes = (
            await session.execute(
                select(AuditLog.action).where(
                    AuditLog.patient_id == patient.id,
                    AuditLog.entity_type == "observation",
                    AuditLog.action == "create",
                )
            )
        ).all()
        assert writes
