"""P3-02 nasal endoscopy: observations, scores, scale snapshot, and the signed lock."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.endoscopy.constants import (
    ADENOID_CODE,
    ENDOSCOPY_STRUCTURE_CODES,
    FINDING_CODES,
    LK_CONCEPT_CODES,
    POLYP_GRADE_CODE,
    PROCEDURE_CODE,
)
from ent.features.endoscopy.models import EndoscopyExam
from ent.features.prescriptions.models import CalculationResultRow
from ent.main import create_app
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_CATALOG: tuple[tuple[str, str, str], ...] = (
    (PROCEDURE_CODE, "procedure", "Nasal endoscopy"),
    *[(code, "qualifier", item) for item, code in LK_CONCEPT_CODES.items()],
    (POLYP_GRADE_CODE, "qualifier", "Polyp grade"),
    (ADENOID_CODE, "qualifier", "Adenoid obstruction"),
    *[(code, "anatomy", code) for code in ENDOSCOPY_STRUCTURE_CODES],
    *[(code, "finding", code) for code in sorted(FINDING_CODES)],
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_endoscopy_scores_recompute_and_freeze_on_sign() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    suffix = new_ulid()[:8].lower()
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
        for code, kind, display in _CATALOG:
            await _ensure_concept(
                client, headers, code=code, kind=kind, display=display
            )

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

        rejected = await client.post(
            "/api/v1/endoscopies",
            headers=headers,
            json=_payload(patient_id, scarring=3),
        )
        assert rejected.status_code == 422, rejected.text
        assert rejected.json()["code"] == "endoscopy.invalid_score"

        sided = _payload(patient_id)
        sided["structures"] = [
            {
                "bodySiteCode": "ANAT.NASAL.VESTIBULE",
                "laterality": "midline",
                "status": "normal",
                "findingCode": "FIND.ENDO.NORMAL",
            }
        ]
        bad_side = await client.post("/api/v1/endoscopies", headers=headers, json=sided)
        assert bad_side.status_code == 422, bad_side.text
        assert bad_side.json()["code"] == "endoscopy.invalid_structure"

        created = await client.post(
            "/api/v1/endoscopies",
            headers=headers,
            json=_payload(patient_id),
        )
        assert created.status_code == 201, created.text
        body = created.json()
        exam_id = body["publicId"]
        procedure_id = body["procedureId"]
        assert body["lundKennedyTotal"] == 0
        assert body["modifiedLkTotal"] == 0
        assert body["polypScale"] == "meltzer"
        assert body["polypGradeRight"] == 0
        assert body["polypGradeLeft"] == 4
        assert body["adenoidObstructionPct"] == 25
        assert body["structures"][0]["finding"]["code"] == "FIND.ENDO.POLYP"
        assert body["structures"][0]["bodySite"]["display"]
        codes = {item["code"] for item in body["scores"]}
        assert "endoscopy.lund_kennedy" in codes
        assert "endoscopy.polyp_grade" in codes
        polyp = next(
            item for item in body["scores"] if item["code"] == "endoscopy.polyp_grade"
        )
        assert polyp["value"] == "0/4"
        assert "Meltzer" in polyp["reference"] or "meltzer" in polyp["formula"]

        updated = await client.put(
            f"/api/v1/endoscopies/{exam_id}",
            headers=headers,
            json=_payload(patient_id, scarring=2, version=1),
        )
        assert updated.status_code == 200, updated.text
        scored = updated.json()
        assert scored["version"] == 2
        assert scored["lundKennedyTotal"] == 2
        assert scored["lundKennedyRight"]["scarring"] == 2
        assert scored["lundKennedyRight"]["total"] == 2
        assert scored["modifiedLkTotal"] == 0

        stale = await client.put(
            f"/api/v1/endoscopies/{exam_id}",
            headers=headers,
            json=_payload(patient_id, scarring=2, version=1),
        )
        assert stale.status_code == 409, stale.text
        assert stale.json()["code"] == "endoscopy.version_conflict"

        scale = await client.put(
            "/api/v1/settings/clinical",
            headers=headers,
            json={"items": [{"key": "polyp_scale", "value": "lildholdt"}]},
        )
        assert scale.status_code == 200, scale.text
        too_high = await client.put(
            f"/api/v1/endoscopies/{exam_id}",
            headers=headers,
            json=_payload(patient_id, scarring=2, polyp_left=4, version=2),
        )
        assert too_high.status_code == 422, too_high.text
        assert too_high.json()["code"] == "endoscopy.invalid_score"

        accepted = await client.put(
            f"/api/v1/endoscopies/{exam_id}",
            headers=headers,
            json=_payload(patient_id, scarring=2, polyp_left=3, version=2),
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["polypScale"] == "lildholdt"
        assert accepted.json()["polypGradeLeft"] == 3

        signed = await client.post(
            f"/api/v1/procedures/{procedure_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        locked = await client.put(
            f"/api/v1/endoscopies/{exam_id}",
            headers=headers,
            json=_payload(
                patient_id, scarring=1, polyp_left=3, version=accepted.json()["version"]
            ),
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "procedure.already_signed"

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/endoscopies",
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert any(item["publicId"] == exam_id for item in listed.json()["items"])
        by_procedure = await client.get(
            f"/api/v1/procedures/{procedure_id}/endoscopy",
            headers=headers,
        )
        assert by_procedure.status_code == 200, by_procedure.text
        assert by_procedure.json()["lundKennedyTotal"] == 2
        missing = await client.get(
            f"/api/v1/endoscopies/{new_ulid()}",
            headers=headers,
        )
        assert missing.status_code == 404, missing.text
        assert missing.json()["code"] == "endoscopy.not_found"

    async with factory() as session:
        exam = (
            await session.execute(
                select(EndoscopyExam).where(EndoscopyExam.public_id == exam_id)
            )
        ).scalar_one()
        count = (
            await session.execute(
                select(func.count())
                .select_from(CalculationResultRow)
                .where(
                    CalculationResultRow.procedure_record_id
                    == exam.procedure_record_id,
                    CalculationResultRow.calculator_code == "endoscopy.lund_kennedy",
                    CalculationResultRow.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        assert int(count) == 3


def _side(*, scarring: int = 0) -> dict[str, int]:
    return {
        "polyps": 0,
        "edema": 0,
        "discharge": 0,
        "scarring": scarring,
        "crusting": 0,
    }


def _payload(
    patient_id: str,
    *,
    scarring: int = 0,
    polyp_left: int = 4,
    version: int | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "patientPublicId": patient_id,
        "performedAt": "2026-06-02T09:15:00",
        "laterality": "bilateral",
        "anesthesia": "topical_spray",
        "setting": "office",
        "scopeType": "rigid_0",
        "decongestantUsed": True,
        "structures": [
            {
                "bodySiteCode": "ANAT.NASAL.SEPTUM",
                "laterality": "midline",
                "status": "abnormal",
                "findingCode": "FIND.ENDO.POLYP",
            }
        ],
        "lundKennedyRight": _side(scarring=scarring),
        "lundKennedyLeft": _side(),
        "polypGradeRight": 0,
        "polypGradeLeft": polyp_left,
        "adenoidObstructionPct": 25,
        "conclusionText": "ostia open",
    }
    if version is not None:
        body["version"] = version
    return body


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
