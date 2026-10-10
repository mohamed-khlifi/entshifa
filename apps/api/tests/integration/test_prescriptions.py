"""P2-08 prescriptions: formulary dosing, safety, issue, and tenancy."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.context import set_clinic_id
from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.features.prescriptions.models import Drug, DrugForm
from ent.features.terminology.models import Concept
from ent.main import create_app
from ent.seeds.formulary import seed_formulary
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures

_DOSING = {
    "mgPerKgPerDay": "80",
    "dosesPerDay": 2,
    "maxMgPerDay": "3000",
    "indications": {
        "otitis": {
            "mgPerKgPerDay": "80",
            "dosesPerDay": 2,
            "maxMgPerDay": "3000",
        }
    },
}


def _amount(value: object) -> Decimal:
    return Decimal(str(value))


def _manual_item(formulary_id: str, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "formularyEntryPublicId": formulary_id,
        "route": "oral",
        "frequencyPerDay": 2,
        "durationDays": 7,
        "doseAmount": "500",
        "doseUnit": "mg",
    }
    body.update(overrides)
    return body


def _calculated_item(formulary_id: str, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "formularyEntryPublicId": formulary_id,
        "route": "oral",
        "frequencyPerDay": 2,
        "durationDays": 7,
        "calculateFromFormulary": True,
        "indicationCode": "otitis",
    }
    body.update(overrides)
    return body


async def _login(client: AsyncClient, email: str, password: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return {
        "headers": {"Authorization": f"Bearer {payload['accessToken']}"},
        "userPublicId": payload["session"]["userPublicId"],
    }


async def _patient(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    birth_date: str,
    first_name: str,
) -> str:
    created = await client.post(
        "/api/v1/patients",
        headers={**headers, "Idempotency-Key": new_ulid()},
        json={
            "firstName": first_name,
            "lastName": f"Rx{new_ulid()[:6]}",
            "birthDate": birth_date,
            "sex": "female",
            "preferredLocale": "en",
        },
    )
    assert created.status_code == 201, created.text
    return str(created.json()["publicId"])


async def _encounter(
    client: AsyncClient, headers: dict[str, str], patient_id: str, site_id: str
) -> str:
    created = await client.post(
        "/api/v1/encounters",
        headers=headers,
        json={
            "patientPublicId": patient_id,
            "sitePublicId": site_id,
            "encounterType": "consultation",
            "startedAt": "2026-10-10T09:00:00",
            "complaints": [
                {
                    "conceptCode": "CC.EAR_PAIN",
                    "laterality": "right",
                    "sortOrder": 0,
                    "isPrimary": True,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    return str(created.json()["publicId"])


def _form_id(drug: dict[str, Any], form: str) -> str:
    matches = [row for row in drug["forms"] if row["form"] == form]
    assert matches, drug
    return str(matches[0]["publicId"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prescription_safety_dosing_and_issue() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
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
            set_clinic_id(int(clinic.id))
            await seed_terminology(session)
            await seed_formulary(session)
            syrup = (
                await session.execute(
                    select(DrugForm)
                    .join(Drug)
                    .where(
                        Drug.code == "DRUG.AMOXICILLIN",
                        DrugForm.form == "syrup",
                        DrugForm.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
            syrup.concentration_mg_per_ml = Decimal("25")
            azithromycin = (
                await session.execute(
                    select(Drug).where(Drug.code == "DRUG.AZITHROMYCIN")
                )
            ).scalar_one()
            azithromycin.pregnancy_category = "caution"
            hearing = (
                await session.execute(
                    select(Concept).where(
                        Concept.code == "H90.3", Concept.deleted_at.is_(None)
                    )
                )
            ).scalar_one()
            other = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["other_clinic_public_id"]
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
                email=f"assistant+{new_ulid().lower()}@test.entshifa.local",
                first_name="Assist",
                last_name="Ant",
                password=fixtures["password"],
            )
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
                email=f"other+{new_ulid().lower()}@test.entshifa.local",
                first_name="Other",
                last_name="Admin",
                password=fixtures["password"],
            )
            await session.commit()
            hearing_id = hearing.public_id
            assistant_email = assistant.email
            other_email = other_admin.email
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, fixtures["admin_email"], fixtures["password"])
        headers = admin["headers"]
        sites = await client.get("/api/v1/sites", headers=headers)
        assert sites.status_code == 200, sites.text
        site_id = sites.json()["items"][0]["publicId"]

        drugs = await client.get("/api/v1/drugs?q=amoxicillin", headers=headers)
        assert drugs.status_code == 200, drugs.text
        assert drugs.json()["page"]["total"] >= 1
        catalog = {row["code"]: row for row in drugs.json()["items"]}
        amox = catalog["DRUG.AMOXICILLIN"]
        amox_concept = amox["concept"]["conceptId"]
        syrup_form = _form_id(amox, "syrup")
        clav = (
            await client.get(
                "/api/v1/drugs?q=DRUG.AMOXICILLIN_CLAVULANATE", headers=headers
            )
        ).json()["items"][0]
        gent = (
            await client.get("/api/v1/drugs?q=DRUG.GENTAMICIN", headers=headers)
        ).json()["items"][0]
        pred = (
            await client.get("/api/v1/drugs?q=DRUG.PREDNISOLONE", headers=headers)
        ).json()["items"][0]
        azith = (
            await client.get("/api/v1/drugs?q=DRUG.AZITHROMYCIN", headers=headers)
        ).json()["items"][0]
        cef = (
            await client.get("/api/v1/drugs?q=DRUG.CEFUROXIME", headers=headers)
        ).json()["items"][0]

        created_formulary = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": syrup_form,
                "brandName": "Amox clinic syrup",
                "price": "12.500",
                "currencyCode": "mad",
                "dosingRules": _DOSING,
            },
        )
        assert created_formulary.status_code == 201, created_formulary.text
        formulary_id = created_formulary.json()["publicId"]
        assert created_formulary.json()["currencyCode"] == "MAD"
        assert created_formulary.json()["dosingRules"]["mgPerKgPerDay"] == "80"
        missing_currency = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": _form_id(amox, "tablet"),
                "brandName": "No currency",
                "price": "1",
            },
        )
        assert missing_currency.status_code == 422, missing_currency.text

        child = await _patient(
            client, headers, birth_date="2020-01-01", first_name="Child"
        )
        child_encounter = await _encounter(client, headers, child, site_id)
        blocked_weight = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "isPediatric": True,
                "items": [_calculated_item(formulary_id)],
            },
        )
        assert blocked_weight.status_code == 409, blocked_weight.text
        assert blocked_weight.json()["code"] == "prescription.pediatric_weight_missing"

        preview = await client.post(
            f"/api/v1/patients/{child}/prescriptions/calculate-dose",
            headers=headers,
            json={
                "formularyEntryPublicId": formulary_id,
                "weightKg": "10",
                "indicationCode": "otitis",
            },
        )
        assert preview.status_code == 200, preview.text
        assert _amount(preview.json()["value"]) == Decimal("400")
        volume_flags = [
            flag for flag in preview.json()["flags"] if flag["code"] == "volume_ml"
        ]
        assert _amount(volume_flags[0]["detail"]["value"]) == Decimal("16")
        unknown_indication = await client.post(
            f"/api/v1/patients/{child}/prescriptions/calculate-dose",
            headers=headers,
            json={
                "formularyEntryPublicId": formulary_id,
                "weightKg": "10",
                "indicationCode": "missing",
            },
        )
        assert unknown_indication.status_code == 422, unknown_indication.text
        assert unknown_indication.json()["code"] == "prescription.dosing_rule_invalid"

        drafted = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers={**headers, "Idempotency-Key": "rx-known-dose"},
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "isPediatric": True,
                "weightKg": "10",
                "items": [_calculated_item(formulary_id)],
            },
        )
        assert drafted.status_code == 201, drafted.text
        body = drafted.json()
        prescription_id = body["publicId"]
        assert _amount(body["items"][0]["doseAmount"]) == Decimal("400")
        assert body["items"][0]["doseUnit"] == "mg"
        assert _amount(body["items"][0]["volumeMl"]) == Decimal("16")
        assert body["items"][0]["dosingEngineVersion"] == "1.0.0"
        assert body["status"] == "draft"
        replay = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers={**headers, "Idempotency-Key": "rx-known-dose"},
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "isPediatric": True,
                "weightKg": "10",
                "items": [_calculated_item(formulary_id)],
            },
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["publicId"] == prescription_id
        mismatch = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers={**headers, "Idempotency-Key": "rx-known-dose"},
            json={
                "encounterPublicId": child_encounter,
                "locale": "fr",
                "isPediatric": True,
                "weightKg": "10",
                "items": [_calculated_item(formulary_id)],
            },
        )
        assert mismatch.status_code == 409, mismatch.text
        assert mismatch.json()["code"] == "prescription.idempotency_mismatch"

        listed = await client.get(
            f"/api/v1/patients/{child}/prescriptions", headers=headers
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["page"]["total"] == 1
        assert listed.json()["items"][0]["publicId"] == prescription_id

        issued = await client.post(
            f"/api/v1/prescriptions/{prescription_id}/issue", headers=headers
        )
        assert issued.status_code == 200, issued.text
        assert issued.json()["status"] == "issued"
        chart = await client.get(f"/api/v1/patients/{child}", headers=headers)
        assert chart.status_code == 200, chart.text
        active = [row for row in chart.json()["medications"] if row["isActive"]]
        assert len(active) == 1
        assert active[0]["source"] == "prescribed_here"
        assert "400" in active[0]["dose"]
        locked = await client.patch(
            f"/api/v1/prescriptions/{prescription_id}",
            headers=headers,
            json={"version": issued.json()["version"], "notes": "too late"},
        )
        assert locked.status_code == 409, locked.text
        assert locked.json()["code"] == "prescription.invalid_status"
        cancelled = await client.post(
            f"/api/v1/prescriptions/{prescription_id}/cancel", headers=headers
        )
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["status"] == "cancelled"
        again = await client.post(
            f"/api/v1/prescriptions/{prescription_id}/cancel", headers=headers
        )
        assert again.status_code == 409, again.text
        chart = await client.get(f"/api/v1/patients/{child}", headers=headers)
        assert all(not row["isActive"] for row in chart.json()["medications"])

        allergy = await client.post(
            f"/api/v1/patients/{child}/allergies",
            headers=headers,
            json={
                "substanceConceptId": amox_concept,
                "category": "drug",
                "severity": "severe",
            },
        )
        assert allergy.status_code == 201, allergy.text
        allergen = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "isPediatric": True,
                "weightKg": "10",
                "items": [_calculated_item(formulary_id)],
            },
        )
        assert allergen.status_code == 409, allergen.text
        assert allergen.json()["code"] == "prescription.allergy_conflict"
        overridden = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "isPediatric": True,
                "weightKg": "10",
                "items": [
                    _calculated_item(
                        formulary_id,
                        safetyOverrides=[
                            {
                                "code": "prescription.allergy_conflict",
                                "reason": "desensitization protocol",
                            }
                        ],
                    )
                ],
            },
        )
        assert overridden.status_code == 201, overridden.text
        recorded = overridden.json()["items"][0]["safetyOverrides"][0]
        assert recorded["reason"] == "desensitization protocol"
        assert recorded["userPublicId"] == admin["userPublicId"]
        assert recorded["code"] == "prescription.allergy_conflict"

        heavy = await _patient(
            client, headers, birth_date="2020-06-01", first_name="Heavy"
        )
        heavy_encounter = await _encounter(client, headers, heavy, site_id)
        above = await client.post(
            f"/api/v1/patients/{heavy}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": heavy_encounter,
                "locale": "en",
                "isPediatric": True,
                "weightKg": "40",
                "items": [_calculated_item(formulary_id)],
            },
        )
        assert above.status_code == 409, above.text
        assert above.json()["code"] == "prescription.dose_above_maximum"
        allowed = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "isPediatric": True,
                "weightKg": "40",
                "items": [
                    _calculated_item(
                        formulary_id,
                        safetyOverrides=[
                            {
                                "code": "prescription.dose_above_maximum",
                                "reason": "severe infection, short course",
                            },
                            {
                                "code": "prescription.allergy_conflict",
                                "reason": "desensitization protocol",
                            },
                        ],
                    )
                ],
            },
        )
        assert allowed.status_code == 201, allowed.text
        assert _amount(allowed.json()["items"][0]["doseAmount"]) == Decimal("1600")

        adult = await _patient(
            client, headers, birth_date="1984-03-03", first_name="Adult"
        )
        adult_encounter = await _encounter(client, headers, adult, site_id)
        clav_entry = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": _form_id(clav, "tablet"),
                "brandName": "Clav tablet",
            },
        )
        assert clav_entry.status_code == 201, clav_entry.text
        gent_entry = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": _form_id(gent, "injection"),
                "brandName": "Gentamicin inj",
            },
        )
        assert gent_entry.status_code == 201, gent_entry.text
        pred_entry = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": _form_id(pred, "tablet"),
                "brandName": "Prednisolone tab",
                "dosingRules": {
                    "taper": {
                        "startMg": "60",
                        "stepMg": "10",
                        "daysPerStep": 2,
                        "minimumMg": "10",
                    }
                },
            },
        )
        assert pred_entry.status_code == 201, pred_entry.text
        azith_entry = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": _form_id(azith, "tablet"),
                "brandName": "Azithromycin tab",
            },
        )
        assert azith_entry.status_code == 201, azith_entry.text

        problem = await client.post(
            f"/api/v1/patients/{adult}/problems",
            headers=headers,
            json={
                "diagnosisConceptId": hearing_id,
                "laterality": "bilateral",
                "status": "active",
            },
        )
        assert problem.status_code == 201, problem.text
        for flag_code in ("pregnancy", "breastfeeding"):
            flag = await client.post(
                f"/api/v1/patients/{adult}/flags",
                headers=headers,
                json={"flagCode": flag_code, "startedOn": "2026-01-01"},
            )
            assert flag.status_code == 201, flag.text

        warned = await client.post(
            f"/api/v1/patients/{adult}/prescriptions/check-safety",
            headers=headers,
            json={
                "items": [
                    _manual_item(gent_entry.json()["publicId"], doseAmount="80"),
                    _manual_item(
                        azith_entry.json()["publicId"],
                        doseAmount="500",
                        frequencyPerDay=1,
                    ),
                    _manual_item(clav_entry.json()["publicId"]),
                    _manual_item(formulary_id),
                ]
            },
        )
        assert warned.status_code == 200, warned.text
        codes = {(row["code"], row["itemIndex"]) for row in warned.json()}
        assert ("prescription.ototoxic_with_hearing_loss", 0) in codes
        assert ("prescription.pregnancy_caution", 1) in codes
        assert ("prescription.breastfeeding_caution", 1) in codes
        assert ("prescription.duplicate_class", 3) in codes

        taper = await client.post(
            f"/api/v1/patients/{adult}/prescriptions/generate-taper",
            headers=headers,
            json={
                "startMg": "60",
                "stepMg": "10",
                "daysPerStep": 2,
                "minimumMg": "10",
            },
        )
        assert taper.status_code == 200, taper.text
        assert taper.json()["value"] == "12"
        tapered = await client.post(
            f"/api/v1/patients/{adult}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": adult_encounter,
                "locale": "en",
                "items": [
                    _manual_item(
                        pred_entry.json()["publicId"],
                        doseAmount="60",
                        frequencyPerDay=1,
                        durationDays=12,
                        useFormularyTaper=True,
                    )
                ],
            },
        )
        assert tapered.status_code == 201, tapered.text
        assert len(tapered.json()["items"][0]["taperSchedule"]) == 12
        assert tapered.json()["items"][0]["taperSchedule"][0]["doseMg"] == "60.000"

        free_text = await client.post(
            f"/api/v1/patients/{adult}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": adult_encounter,
                "locale": "en",
                "notes": "compounded drops",
                "items": [
                    {
                        "freeTextName": "Compounded ear drops",
                        "route": "otic",
                        "frequencyPerDay": 3,
                        "durationDays": 5,
                        "doseAmount": "3",
                        "doseUnit": "drop",
                    }
                ],
            },
        )
        assert free_text.status_code == 201, free_text.text
        assert free_text.json()["safetyAlerts"][0]["code"] == (
            "prescription.unstructured_item"
        )
        edited = await client.patch(
            f"/api/v1/prescriptions/{free_text.json()['publicId']}",
            headers=headers,
            json={
                "version": free_text.json()["version"],
                "notes": "still compounded",
                "items": [
                    {
                        "freeTextName": "Compounded ear drops",
                        "route": "otic",
                        "frequencyPerDay": 2,
                        "durationDays": 5,
                        "doseAmount": "3",
                        "doseUnit": "drop",
                    }
                ],
            },
        )
        assert edited.status_code == 200, edited.text
        assert edited.json()["notes"] == "still compounded"
        assert edited.json()["version"] == free_text.json()["version"] + 1
        stale = await client.patch(
            f"/api/v1/prescriptions/{free_text.json()['publicId']}",
            headers=headers,
            json={
                "version": free_text.json()["version"],
                "items": [
                    {
                        "freeTextName": "Compounded ear drops",
                        "route": "otic",
                        "frequencyPerDay": 2,
                        "durationDays": 5,
                        "doseAmount": "3",
                        "doseUnit": "drop",
                    }
                ],
            },
        )
        assert stale.status_code == 409, stale.text
        assert stale.json()["code"] == "prescription.version_conflict"

        template = await client.post(
            "/api/v1/prescription-templates",
            headers=headers,
            json={
                "code": "otitis_media",
                "nameKey": "prescription.template.otitis",
                "isPediatric": True,
                "items": [
                    {
                        "freeTextName": "Amoxicillin syrup",
                        "route": "oral",
                        "frequencyPerDay": 2,
                        "durationDays": 7,
                        "doseAmount": "400",
                        "doseUnit": "mg",
                    }
                ],
            },
        )
        assert template.status_code == 201, template.text
        templates = await client.get("/api/v1/prescription-templates", headers=headers)
        assert templates.status_code == 200, templates.text
        assert templates.json()["page"]["total"] >= 1

        cef_entry = await client.post(
            "/api/v1/formulary",
            headers=headers,
            json={
                "drugFormPublicId": _form_id(cef, "tablet"),
                "brandName": "Cefuroxime tab",
            },
        )
        assert cef_entry.status_code == 201, cef_entry.text
        visible = await client.get("/api/v1/formulary?q=Cefuroxime", headers=headers)
        assert visible.status_code == 200, visible.text
        assert visible.json()["items"][0]["publicId"] == cef_entry.json()["publicId"], (
            visible.json(),
            cef_entry.json()["publicId"],
        )
        hidden = await client.patch(
            f"/api/v1/formulary/{cef_entry.json()['publicId']}",
            headers=headers,
            json={"version": cef_entry.json()["version"], "isAvailable": False},
        )
        assert hidden.status_code == 200, hidden.text
        catalog_after = await client.get(
            "/api/v1/formulary?q=Cefuroxime", headers=headers
        )
        assert catalog_after.status_code == 200, catalog_after.text
        assert catalog_after.json()["items"] == []
        refused = await client.post(
            f"/api/v1/patients/{adult}/prescriptions",
            headers=headers,
            json={
                "encounterPublicId": adult_encounter,
                "locale": "en",
                "items": [_manual_item(cef_entry.json()["publicId"])],
            },
        )
        assert refused.status_code == 404, refused.text
        assert refused.json()["code"] == "prescription.formulary_not_found"

        signed = await client.post(
            f"/api/v1/encounters/{adult_encounter}/sign",
            headers=headers,
            json={"role": "clinician"},
        )
        assert signed.status_code == 200, signed.text
        locked_issue = await client.post(
            f"/api/v1/prescriptions/{free_text.json()['publicId']}/issue",
            headers=headers,
        )
        assert locked_issue.status_code == 409, locked_issue.text
        assert locked_issue.json()["code"] == "encounter.already_signed"

        outsider = await _login(client, other_email, fixtures["password"])
        hidden_rx = await client.get(
            f"/api/v1/prescriptions/{prescription_id}",
            headers=outsider["headers"],
        )
        assert hidden_rx.status_code == 404, hidden_rx.text
        assert hidden_rx.json()["code"] == "prescription.not_found"
        hidden_formulary = await client.patch(
            f"/api/v1/formulary/{formulary_id}",
            headers=outsider["headers"],
            json={"version": 1, "brandName": "Other clinic"},
        )
        assert hidden_formulary.status_code == 404, hidden_formulary.text
        assert hidden_formulary.json()["code"] == "prescription.formulary_not_found"

        assistant_session = await _login(client, assistant_email, fixtures["password"])
        denied = await client.get("/api/v1/drugs", headers=assistant_session["headers"])
        assert denied.status_code == 403, denied.text
        denied_write = await client.post(
            f"/api/v1/patients/{child}/prescriptions",
            headers=assistant_session["headers"],
            json={
                "encounterPublicId": child_encounter,
                "locale": "en",
                "items": [
                    {
                        "freeTextName": "Should not save",
                        "route": "oral",
                        "frequencyPerDay": 1,
                        "durationDays": 1,
                        "doseAmount": "1",
                        "doseUnit": "mg",
                    }
                ],
            },
        )
        assert denied_write.status_code == 403, denied_write.text
