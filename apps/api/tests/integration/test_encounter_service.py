"""P2-02 encounters: sign, lock, addendum, copy-forward, and version conflicts."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.audit.models import AccessLog, AuditLog
from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.encounters.exceptions import EncounterLockedError
from ent.features.encounters.models import Encounter, EncounterTemplate
from ent.features.encounters.repository import EncounterRepository
from ent.features.terminology.models import CodeSystem, Concept
from ent.features.users.models import User
from ent.main import create_app
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_signed_encounter_is_immutable_and_versioned() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    complaint_code = f"CC.EAR_PAIN.{suffix}"
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await seed_terminology(session)
            clinic = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["clinic_public_id"]
                    )
                )
            ).scalar_one()
            doctor = (
                await session.execute(
                    select(User).where(User.public_id == fixtures["doctor_public_id"])
                )
            ).scalar_one()
            system = (await session.execute(select(CodeSystem).limit(1))).scalar_one()
            session.add(
                Concept(
                    public_id=new_ulid(),
                    code_system_id=system.id,
                    code=complaint_code,
                    kind="finding",
                    sort_order=0,
                )
            )
            clinic_template = EncounterTemplate(
                public_id=new_ulid(),
                clinic_id=clinic.id,
                code=f"clinic-{suffix}",
                name_key="encounters.template.clinic",
                trigger_concept_ids=[],
                config={"historyFields": ["onset"]},
                is_active=True,
            )
            system_template = EncounterTemplate(
                public_id=new_ulid(),
                clinic_id=None,
                code=f"system-{suffix}",
                name_key="encounters.template.system",
                trigger_concept_ids=[],
                config={"historyFields": ["onset"]},
                is_active=True,
            )
            doctor_template = EncounterTemplate(
                public_id=new_ulid(),
                clinic_id=clinic.id,
                user_id=doctor.id,
                code=f"doctor-{suffix}",
                name_key="encounters.template.doctor",
                trigger_concept_ids=[],
                config={"historyFields": ["onset"]},
                is_active=True,
            )
            session.add_all([clinic_template, system_template, doctor_template])
            await session.commit()
            clinic_id = int(clinic.id)
            template_ids = {
                "clinic": clinic_template.public_id,
                "system": system_template.public_id,
                "doctor": doctor_template.public_id,
            }
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
        sites = await client.get("/api/v1/sites", headers=headers)
        assert sites.status_code == 200, sites.text
        site_id = sites.json()["items"][0]["publicId"]
        created_patient = await client.post(
            "/api/v1/patients",
            headers=headers,
            json={
                "firstName": "Visit",
                "lastName": f"Chart{suffix}",
                "birthDate": "1984-03-03",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert created_patient.status_code == 201, created_patient.text
        patient_id = created_patient.json()["publicId"]

        unknown = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json=_create_body(patient_id, site_id, complaint_code="MISSING.CODE"),
        )
        assert unknown.status_code == 422
        assert unknown.json()["code"] == "validation_failed"

        hidden_template = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json=_create_body(
                patient_id,
                site_id,
                complaint_code=complaint_code,
                template_id=template_ids["doctor"],
            ),
        )
        assert hidden_template.status_code == 404

        created = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json=_create_body(
                patient_id,
                site_id,
                complaint_code=complaint_code,
                template_id=template_ids["clinic"],
            ),
        )
        assert created.status_code == 201, created.text
        visit = created.json()
        assert visit["status"] == "draft"
        assert visit["version"] == 1
        assert visit["templatePublicId"] == template_ids["clinic"]
        assert visit["complaints"][0]["isPrimary"] is True
        assert visit["complaints"][0]["concept"]["code"] == complaint_code
        encounter_id = visit["publicId"]

        loaded = await client.get(f"/api/v1/encounters/{encounter_id}", headers=headers)
        assert loaded.status_code == 200, loaded.text
        listed = await client.get(
            f"/api/v1/patients/{patient_id}/encounters", headers=headers
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["page"]["total"] == 1

        patched = await client.patch(
            f"/api/v1/encounters/{encounter_id}",
            headers=headers,
            json={"version": 1, "historyText": "sudden onset"},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["version"] == 2
        assert patched.json()["historyText"] == "sudden onset"

        conflict = await client.patch(
            f"/api/v1/encounters/{encounter_id}",
            headers=headers,
            json={"version": 1, "historyText": "overwrite"},
        )
        assert conflict.status_code == 409
        body = conflict.json()
        assert body["code"] == "encounter.version_conflict"
        assert body["context"]["serverVersion"] == 2
        assert body["context"]["clientVersion"] == 1
        current = await client.get(
            f"/api/v1/encounters/{encounter_id}", headers=headers
        )
        assert current.json()["historyText"] == "sudden onset"

        signed = await client.post(
            f"/api/v1/encounters/{encounter_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        signed_body = signed.json()
        assert signed_body["status"] == "signed"
        assert len(signed_body["lockedHash"]) == 64
        assert signed_body["signatures"][0]["contentHash"] == signed_body["lockedHash"]
        assert signed_body["signatures"][0]["role"] == "clinician"
        assert signed_body["signedByPublicId"] == visit["clinicianPublicId"]

        locked = await client.patch(
            f"/api/v1/encounters/{encounter_id}",
            headers=headers,
            json={"version": signed_body["version"], "historyText": "after sign"},
        )
        assert locked.status_code == 409
        assert locked.json()["code"] == "encounter.already_signed"

        again = await client.post(
            f"/api/v1/encounters/{encounter_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert again.status_code == 409
        assert again.json()["code"] == "encounter.already_signed"

        addendum = await client.post(
            f"/api/v1/encounters/{encounter_id}/addenda",
            headers=headers,
            json={"body": "Correction: onset was two days, not sudden."},
        )
        assert addendum.status_code == 201, addendum.text
        amended = addendum.json()
        assert amended["status"] == "amended"
        assert amended["addenda"][0]["body"].startswith("Correction:")
        assert amended["addenda"][0]["authorPublicId"] == visit["clinicianPublicId"]
        assert amended["lockedHash"] == signed_body["lockedHash"]

        copied = await client.post(
            f"/api/v1/encounters/{encounter_id}/copy-forward",
            headers=headers,
            json={"startedAt": "2026-07-01T09:00:00"},
        )
        assert copied.status_code == 201, copied.text
        copy_body = copied.json()
        assert copy_body["status"] == "draft"
        assert copy_body["previousEncounterPublicId"] == encounter_id
        assert copy_body["historyText"] == "sudden onset"
        assert copy_body["complaints"][0]["concept"]["code"] == complaint_code
        assert copy_body["publicId"] != encounter_id

        early_addendum = await client.post(
            f"/api/v1/encounters/{copy_body['publicId']}/addenda",
            headers=headers,
            json={"body": "too soon"},
        )
        assert early_addendum.status_code == 422
        assert early_addendum.json()["code"] == "encounter.invalid_transition"

        system_visit = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json=_create_body(
                patient_id,
                site_id,
                complaint_code=complaint_code,
                template_id=template_ids["system"],
            ),
        )
        assert system_visit.status_code == 201, system_visit.text
        assert system_visit.json()["templatePublicId"] == template_ids["system"]

        bad_range = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json={
                **_create_body(patient_id, site_id, complaint_code=complaint_code),
                "endedAt": "2026-05-01T08:00:00",
            },
        )
        assert bad_range.status_code == 422

        missing = await client.get(f"/api/v1/encounters/{new_ulid()}", headers=headers)
        assert missing.status_code == 404
        assert missing.json()["code"] == "encounter.not_found"

    async with factory() as session:
        repo = EncounterRepository(session, clinic_id=clinic_id)
        row = await repo.get_detail(encounter_id)
        assert row is not None
        with pytest.raises(EncounterLockedError):
            repo.apply_draft_changes(row, {"history_text": "repository rewrite"})
        row.history_text = "listener rewrite"
        with pytest.raises(EncounterLockedError):
            await session.flush()
        await session.rollback()
        patient_row = (
            await session.execute(
                select(Encounter).where(Encounter.public_id == encounter_id)
            )
        ).scalar_one()
        reads = (
            (
                await session.execute(
                    select(AccessLog.action).where(
                        AccessLog.patient_id == patient_row.patient_id,
                        AccessLog.entity_type == "encounter",
                    )
                )
            )
            .scalars()
            .all()
        )
        writes = (
            (
                await session.execute(
                    select(AuditLog.action).where(
                        AuditLog.entity_type == "encounter",
                        AuditLog.entity_public_id == encounter_id,
                    )
                )
            )
            .scalars()
            .all()
        )
    assert "read" in reads
    assert "list" in reads
    assert "create" in writes
    assert "update" in writes


def _create_body(
    patient_id: str,
    site_id: str,
    *,
    complaint_code: str,
    template_id: str | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "patientPublicId": patient_id,
        "sitePublicId": site_id,
        "encounterType": "consultation",
        "startedAt": "2026-06-01T09:00:00",
        "chiefComplaintSummary": "ear pain",
        "complaints": [
            {
                "conceptCode": complaint_code,
                "laterality": "right",
                "durationText": "2 days",
                "sortOrder": 1,
            }
        ],
    }
    if template_id is not None:
        body["templatePublicId"] = template_id
    return body
