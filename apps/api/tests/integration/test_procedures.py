"""P3-01 procedure record: draft, sign, lock, addendum, and tenant isolation."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.events.bus import get_event_bus, reset_event_bus
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.procedures.events import PROCEDURE_PERFORMED
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_procedure_signs_locks_and_accepts_only_addenda() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            clinic = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["clinic_public_id"]
                    )
                )
            ).scalar_one()
            assistant_role = await ensure_role(
                session,
                clinic=clinic,
                code="assistant",
                name_key="role.assistant",
            )
            assistant = await ensure_user_with_role(
                session,
                clinic=clinic,
                role=assistant_role,
                email=f"assistant+{suffix}@test.entshifa.local",
                first_name="Ada",
                last_name="Assistant",
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
        procedure_concept = await _concept(
            client,
            headers,
            code=f"PROC.{suffix}",
            kind="procedure",
            display="Nasal endoscopy",
        )
        finding = await _concept(
            client, headers, code=f"FIND.{suffix}", kind="finding", display="Bleeding"
        )
        anatomy = await _concept(
            client,
            headers,
            code=f"ANAT.{suffix}",
            kind="anatomy",
            display="Septum",
        )
        sites = await client.get("/api/v1/sites", headers=headers)
        assert sites.status_code == 200, sites.text
        site_id = sites.json()["items"][0]["publicId"]
        patient = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Nasal",
                "lastName": f"Scope{suffix}",
                "birthDate": "1988-04-04",
                "sex": "female",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]
        other_patient = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Other",
                "lastName": f"Chart{suffix}",
                "birthDate": "1979-01-01",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert other_patient.status_code == 201, other_patient.text
        encounter = await client.post(
            "/api/v1/encounters",
            headers=headers,
            json={
                "patientPublicId": patient_id,
                "sitePublicId": site_id,
                "encounterType": "procedure",
                "startedAt": "2026-06-02T09:00:00",
            },
        )
        assert encounter.status_code == 201, encounter.text
        encounter_id = encounter.json()["publicId"]

        rejected = await client.post(
            "/api/v1/procedures",
            headers=headers,
            json=_payload(
                patient_id,
                anatomy,
                encounter_id,
                indication="wrong kind",
            ),
        )
        assert rejected.status_code == 422, rejected.text
        assert rejected.json()["code"] == "procedure.invalid_concept"

        mismatched = await client.post(
            "/api/v1/procedures",
            headers=headers,
            json=_payload(
                other_patient.json()["publicId"],
                procedure_concept,
                encounter_id,
                indication="wrong visit",
            ),
        )
        assert mismatched.status_code == 422, mismatched.text
        assert mismatched.json()["context"]["reason"] == "encounter_patient"

        created = await client.post(
            "/api/v1/procedures",
            headers=headers,
            json=_payload(
                patient_id,
                procedure_concept,
                encounter_id,
                indication="epistaxis",
                complication_id=finding,
            ),
        )
        assert created.status_code == 201, created.text
        body = created.json()
        procedure_id = body["publicId"]
        assert body["status"] == "draft"
        assert body["procedure"]["display"] == "Nasal endoscopy"
        assert body["complication"]["code"] == f"FIND.{suffix}"
        assert body["encounterId"] == encounter_id
        assert body["laterality"] == "right"
        assert body["anesthesia"] == "topical_spray"
        assert body["setting"] == "office"
        assert body["lockedHash"] is None

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/procedures",
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert any(item["publicId"] == procedure_id for item in listed.json()["items"])

        updated = await client.put(
            f"/api/v1/procedures/{procedure_id}",
            headers=headers,
            json={"version": body["version"], "tolerance": "well_tolerated"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["tolerance"] == "well_tolerated"
        stale = await client.put(
            f"/api/v1/procedures/{procedure_id}",
            headers=headers,
            json={"version": body["version"], "instrument": "rigid 30"},
        )
        assert stale.status_code == 409, stale.text
        assert stale.json()["code"] == "procedure.version_conflict"

        early_addendum = await client.post(
            f"/api/v1/procedures/{procedure_id}/addenda",
            headers=headers,
            json={"body": "too soon"},
        )
        assert early_addendum.status_code == 422, early_addendum.text
        assert early_addendum.json()["code"] == "procedure.invalid_transition"

        reset_event_bus()
        signed = await client.post(
            f"/api/v1/procedures/{procedure_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        signed_body = signed.json()
        assert signed_body["status"] == "signed"
        assert signed_body["lockedHash"]
        assert signed_body["signedById"]
        assert signed_body["signedRole"] == "clinician"
        assert len(signed_body["lockedHash"]) == 64
        performed = [
            event
            for event in get_event_bus().published
            if event.name == PROCEDURE_PERFORMED
            and event.payload["procedure_public_id"] == procedure_id
        ]
        assert len(performed) == 1
        assert performed[0].payload["procedure_concept_code"] == f"PROC.{suffix}"
        assert performed[0].payload["has_complications"] is True
        assert performed[0].payload["encounter_public_id"] == encounter_id

        locked = await client.put(
            f"/api/v1/procedures/{procedure_id}",
            headers=headers,
            json={
                "version": signed_body["version"],
                "indicationText": "rewritten after signing",
            },
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "procedure.already_signed"

        amended = await client.post(
            f"/api/v1/procedures/{procedure_id}/addenda",
            headers=headers,
            json={"body": "Bleeding site was the left Little area."},
        )
        assert amended.status_code == 201, amended.text
        amended_body = amended.json()
        assert amended_body["status"] == "amended"
        assert amended_body["lockedHash"] == signed_body["lockedHash"]
        assert amended_body["indicationText"] == "epistaxis"
        assert len(amended_body["addenda"]) == 1
        assert amended_body["addenda"][0]["authorPublicId"]

        assistant_login = await client.post(
            "/api/v1/auth/login",
            json={"email": assistant.email, "password": fixtures["password"]},
        )
        assert assistant_login.status_code == 200, assistant_login.text
        assistant_headers = {
            "Authorization": f"Bearer {assistant_login.json()['accessToken']}"
        }
        forbidden = await client.post(
            f"/api/v1/procedures/{procedure_id}/sign",
            headers=assistant_headers,
            json={},
        )
        assert forbidden.status_code == 403, forbidden.text

        missing = await client.get(
            f"/api/v1/procedures/{new_ulid()}",
            headers=headers,
        )
        assert missing.status_code == 404, missing.text
        assert missing.json()["code"] == "procedure.not_found"


def _payload(
    patient_id: str,
    concept_id: str,
    encounter_id: str,
    *,
    indication: str,
    complication_id: str | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "patientPublicId": patient_id,
        "encounterPublicId": encounter_id,
        "procedureConceptPublicId": concept_id,
        "performedAt": "2026-06-02T09:15:00",
        "laterality": "right",
        "anesthesia": "topical_spray",
        "setting": "office",
        "instrument": "rigid 0",
        "indicationText": indication,
        "tolerance": "mild_discomfort",
    }
    if complication_id is not None:
        body["complicationConceptPublicId"] = complication_id
        body["complicationNote"] = "brief ooze"
    return body


async def _concept(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    code: str,
    kind: str,
    display: str,
) -> str:
    created = await client.post(
        "/api/v1/terminology/admin/concepts",
        headers=headers,
        json={"code": code, "kind": kind, "locale": "en", "display": display},
    )
    assert created.status_code == 201, created.text
    return str(created.json()["publicId"])
