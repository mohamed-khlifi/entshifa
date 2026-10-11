"""P3-04 laryngoscopy: observations, scores, and the signed lock."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.laryngoscopy.constants import PAS_CODE, PROCEDURE_CODE
from ent.features.terminology.models import CodeSystem, Concept, ConceptTranslation
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.seeds.laryngoscopy import seed_laryngoscopy
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_laryngoscopy_scores_recompute_and_freeze_on_sign() -> None:
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
                email=f"larynx-other+{suffix}@test.entshifa.local",
                first_name="Other",
                last_name="Clinic",
                password=fixtures["password"],
            )
            await _ensure_global_catalog(session)
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

        patient = await client.post(
            "/api/v1/patients",
            headers={**headers, "Idempotency-Key": new_ulid()},
            json={
                "firstName": "Vocal",
                "lastName": f"Fold{suffix}",
                "birthDate": "1979-03-03",
                "sex": "male",
                "preferredLocale": "en",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["publicId"]

        rejected = await client.post(
            "/api/v1/laryngoscopies",
            headers=headers,
            json=_payload(
                patient_id,
                vocalFoldRight={"mobility": "immobile"},
            ),
        )
        assert rejected.status_code == 422, rejected.text
        assert rejected.json()["code"] == "laryngoscopy.invalid_exam", rejected.text

        created = await client.post(
            "/api/v1/laryngoscopies",
            headers=headers,
            json=_payload(patient_id),
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["rfsScore"] == 0
        assert body["grbas"]["total"] == 5
        assert body["pasScore"] == 2
        assert body["feesPerformed"] is True
        assert body["stroboscopyPerformed"] is True
        assert body["vocalFoldRight"]["mobility"] == "immobile"
        assert body["vocalFoldRight"]["position"] == "paramedian"
        assert body["structures"][0]["finding"]["code"] == "FIND.LARYNX.NORMAL"
        assert body["lesions"][0]["finding"]["code"] == "FIND.LARYNX.NODULE"
        assert body["consistencies"][0]["code"] == "FEES.CONSISTENCY.THIN"
        assert body["residueSites"][0]["code"] == "ANAT.LARYNX.VALLECULA"
        assert {item["code"] for item in body["scores"]} == {
            "laryngoscopy.reflux_finding_score",
            "laryngoscopy.grbas",
            "laryngoscopy.penetration_aspiration",
        }
        exam_id = body["publicId"]
        procedure_id = body["procedureId"]

        listed = await client.get(
            f"/api/v1/patients/{patient_id}/laryngoscopies",
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["page"]["total"] == 1

        by_procedure = await client.get(
            f"/api/v1/procedures/{procedure_id}/laryngoscopy",
            headers=headers,
        )
        assert by_procedure.status_code == 200, by_procedure.text
        assert by_procedure.json()["publicId"] == exam_id

        missing = await client.get(
            f"/api/v1/laryngoscopies/{new_ulid()}",
            headers=headers,
        )
        assert missing.status_code == 404
        assert missing.json()["code"] == "laryngoscopy.not_found"

        signed = await client.post(
            f"/api/v1/procedures/{procedure_id}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        locked = await client.put(
            f"/api/v1/laryngoscopies/{exam_id}",
            headers=headers,
            json=_payload(patient_id, version=body["version"]),
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "procedure.already_signed"

        other_login = await client.post(
            "/api/v1/auth/login",
            json={"email": other_admin.email, "password": fixtures["password"]},
        )
        assert other_login.status_code == 200, other_login.text
        other_headers = {"Authorization": f"Bearer {other_login.json()['accessToken']}"}
        hidden = await client.get(
            f"/api/v1/laryngoscopies/{exam_id}",
            headers=other_headers,
        )
        assert hidden.status_code == 404
        assert hidden.json()["code"] == "laryngoscopy.not_found"


def _payload(patient_id: str, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "patientPublicId": patient_id,
        "performedAt": "2026-10-11T10:00:00Z",
        "scopeType": "flexible_fiberoptic",
        "vocalFoldRight": {"mobility": "immobile", "position": "paramedian"},
        "vocalFoldLeft": {"mobility": "normal"},
        "glotticClosure": "posterior_gap",
        "supraglotticPattern": "none",
        "structures": [
            {
                "bodySiteCode": "ANAT.LARYNX.EPIGLOTTIS",
                "laterality": "midline",
                "status": "normal",
                "findingCode": "FIND.LARYNX.NORMAL",
            }
        ],
        "lesions": [
            {
                "laterality": "right",
                "thirdCode": "QUAL.VF.THIRD.ANTERIOR",
                "surfaceCode": "QUAL.VF.SURFACE.FREE_EDGE",
                "findingCode": "FIND.LARYNX.NODULE",
                "sizeMm": 2,
            }
        ],
        "stroboscopy": {
            "symmetry": "asymmetric",
            "periodicity": "irregular",
            "amplitudeRight": "reduced",
            "amplitudeLeft": "normal",
            "mucosalWaveRight": "reduced",
            "mucosalWaveLeft": "normal",
            "phaseClosure": "predominantly_open",
            "nonVibratingSegment": "right",
        },
        "refluxFindingScore": {
            "subglotticEdema": 0,
            "ventricularObliteration": 0,
            "erythema": 0,
            "vocalFoldEdema": 0,
            "diffuseLaryngealEdema": 0,
            "posteriorCommissureHypertrophy": 0,
            "granuloma": 0,
            "thickEndolaryngealMucus": 0,
        },
        "grbas": {
            "grade": 1,
            "roughness": 1,
            "breathiness": 1,
            "asthenia": 1,
            "strain": 1,
        },
        "fees": {
            "pasScore": 2,
            "consistencies": ["FEES.CONSISTENCY.THIN"],
            "residueSiteCodes": ["ANAT.LARYNX.VALLECULA"],
        },
    }
    body.update(overrides)
    return body


async def _ensure_global_catalog(session: AsyncSession) -> None:
    """Load the shared laryngoscopy catalog into the internal code system."""

    system = (
        await session.execute(
            select(CodeSystem).where(
                CodeSystem.code == "INTERNAL",
                CodeSystem.deleted_at.is_(None),
            )
        )
    ).scalar_one()
    rows = list(
        (
            await session.scalars(
                select(Concept).where(
                    Concept.deleted_at.is_(None),
                    Concept.code_system_id == system.id,
                    or_(
                        Concept.code.like("ANAT.LARYNX%"),
                        Concept.code.like("FIND.LARYNX%"),
                        Concept.code.like("SCORE.RFS%"),
                        Concept.code.like("SCORE.GRBAS%"),
                        Concept.code == PAS_CODE,
                        Concept.code.like("FEES.CONSISTENCY%"),
                        Concept.code.like("QUAL.VF%"),
                        Concept.code == PROCEDURE_CODE,
                        Concept.code.in_(
                            (
                                "ANAT.NASAL_CAVITY",
                                "ANAT.NASAL.NASOPHARYNX",
                            )
                        ),
                    ),
                )
            )
        ).all()
    )
    concept_ids = [int(row.id) for row in rows]
    for row in rows:
        row.clinic_id = None
    if concept_ids:
        translations = (
            await session.scalars(
                select(ConceptTranslation).where(
                    ConceptTranslation.concept_id.in_(concept_ids)
                )
            )
        ).all()
        for translation in translations:
            translation.clinic_id = None
    await seed_laryngoscopy(session, system, {row.code: row for row in rows})
