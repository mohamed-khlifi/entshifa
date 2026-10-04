"""Integration tests for P2-03: Visit templates and chief complaint routing."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic
from ent.main import create_app
from ent.seeds.encounter_templates import seed_encounter_templates
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.support.clinic_seed import seed_clinic_admin_fixtures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_encounter_template_routing_and_isolation() -> None:
    """Verifies Appendix B complaint routing, doctor-level overrides, and clinic isolation."""
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    transport = ASGITransport(app=app)

    async with factory() as session:
        fixtures = await seed_clinic_admin_fixtures(session)
        await seed_terminology(session)
        await seed_encounter_templates(session)
        await session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login doctor
        doc_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": fixtures["doctor_email"],
                "password": fixtures["password"],
            },
        )
        assert doc_login.status_code == 200, doc_login.text
        clinic_token = doc_login.json()["accessToken"]

        # 1. Routing by chief complaint: Nasal obstruction vs Vertigo
        nasal_res = await client.post(
            "/api/v1/encounter-templates/route",
            headers={"Authorization": f"Bearer {clinic_token}"},
            json={"complaintCodes": ["CC.NASAL_OBSTRUCTION"]},
        )
        assert nasal_res.status_code == 200, nasal_res.text
        nasal_data = nasal_res.json()
        assert nasal_data["code"] == "TPL.NASAL_OBSTRUCTION"
        assert "nose" in nasal_data["config"]["examSections"]
        assert "endoscopy" in nasal_data["config"]["examSections"]
        assert "snot22" in nasal_data["config"]["suggestedInstruments"]

        vertigo_res = await client.post(
            "/api/v1/encounter-templates/route",
            headers={"Authorization": f"Bearer {clinic_token}"},
            json={"complaintCodes": ["CC.VERTIGO"]},
        )
        assert vertigo_res.status_code == 200, vertigo_res.text
        vertigo_data = vertigo_res.json()
        assert vertigo_data["code"] == "TPL.VERTIGO"
        assert "vestibular_exam" in vertigo_data["config"]["examSections"]
        assert "dhi" in vertigo_data["config"]["suggestedInstruments"]

        # 2. Doctor override: Doctor customizes history fields for nasal obstruction
        override_payload = {
            "config": {
                "historyFields": [
                    {
                        "id": "custom_obstruction_question",
                        "labelKey": "custom.label",
                        "fieldType": "boolean",
                        "required": True,
                    }
                ],
                "examSections": ["nose", "endoscopy"],
                "suggestedInstruments": ["snot22"],
                "suggestedTests": ["ct_sinuses"],
                "suggestedDocuments": [],
                "favoriteDiagnoses": ["J34.2"],
                "defaultFollowUpDays": 28,
            }
        }
        override_res = await client.post(
            "/api/v1/encounter-templates/TPL.NASAL_OBSTRUCTION/override?scope=doctor",
            headers={"Authorization": f"Bearer {clinic_token}"},
            json=override_payload,
        )
        assert override_res.status_code == 200, override_res.text
        override_data = override_res.json()
        assert override_data["scope"] == "doctor"
        assert override_data["config"]["defaultFollowUpDays"] == 28

        # 3. Same doctor routes again and gets the overridden version
        routed_override_res = await client.post(
            "/api/v1/encounter-templates/route",
            headers={"Authorization": f"Bearer {clinic_token}"},
            json={"complaintCodes": ["CC.NASAL_OBSTRUCTION"]},
        )
        assert routed_override_res.status_code == 200
        routed_data = routed_override_res.json()
        assert routed_data["scope"] == "doctor"
        assert (
            routed_data["config"]["historyFields"][0]["id"]
            == "custom_obstruction_question"
        )

        # 4. Another doctor in the same clinic is unaffected
        from ent.seeds.identity import (
            ensure_role,
            ensure_user_with_role,
        )

        async with factory() as session:
            clinic = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["clinic_public_id"]
                    )
                )
            ).scalar_one()
            doctor_role = await ensure_role(
                session, clinic=clinic, code="doctor", name_key="role.doctor"
            )
            doc2_email = f"doctor2+{new_ulid()[:6]}@test.entshifa.local"
            await ensure_user_with_role(
                session,
                clinic=clinic,
                role=doctor_role,
                email=doc2_email,
                first_name="Doc2",
                last_name="Tor2",
                password=fixtures["password"],
            )
            await session.commit()

        doc2_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": doc2_email,
                "password": fixtures["password"],
            },
        )
        assert doc2_login.status_code == 200, doc2_login.text
        second_token = doc2_login.json()["accessToken"]

        doc2_res = await client.post(
            "/api/v1/encounter-templates/route",
            headers={"Authorization": f"Bearer {second_token}"},
            json={"complaintCodes": ["CC.NASAL_OBSTRUCTION"]},
        )
        assert doc2_res.status_code == 200
        doc2_data = doc2_res.json()
        # Doctor 2 gets the system template, unaffected by Doctor 1's override
        assert doc2_data["scope"] == "system"
        assert doc2_data["config"]["defaultFollowUpDays"] == 42

        # 5. Doctor 1 resets override
        reset_res = await client.delete(
            "/api/v1/encounter-templates/TPL.NASAL_OBSTRUCTION/override?scope=doctor",
            headers={"Authorization": f"Bearer {clinic_token}"},
        )
        assert reset_res.status_code == 204

        # Doctor 1 now receives system template again
        post_reset_res = await client.post(
            "/api/v1/encounter-templates/route",
            headers={"Authorization": f"Bearer {clinic_token}"},
            json={"complaintCodes": ["CC.NASAL_OBSTRUCTION"]},
        )
        assert post_reset_res.status_code == 200
        assert post_reset_res.json()["scope"] == "system"

        # 6. Tenant isolation: Other clinic doctor cannot access or route to Clinic 1's custom overrides
        other_doc_email = f"other_doc+{new_ulid()[:6]}@test.entshifa.local"
        async with factory() as session:
            other_clinic = (
                await session.execute(
                    select(Clinic).where(
                        Clinic.public_id == fixtures["other_clinic_public_id"]
                    )
                )
            ).scalar_one()
            other_role = await ensure_role(
                session, clinic=other_clinic, code="doctor", name_key="role.doctor"
            )
            await ensure_user_with_role(
                session,
                clinic=other_clinic,
                role=other_role,
                email=other_doc_email,
                first_name="Other",
                last_name="Doctor",
                password=fixtures["password"],
            )
            await session.commit()

        # Create a clinic-level override in Clinic 1
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": fixtures["admin_email"],
                "password": fixtures["password"],
            },
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]
        clinic_override_payload = {
            "config": {
                "historyFields": [],
                "examSections": ["nose"],
                "suggestedInstruments": [],
                "suggestedTests": [],
                "suggestedDocuments": [],
                "favoriteDiagnoses": [],
                "defaultFollowUpDays": 99,
            }
        }
        c_res = await client.post(
            "/api/v1/encounter-templates/TPL.NASAL_OBSTRUCTION/override?scope=clinic",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=clinic_override_payload,
        )
        assert c_res.status_code == 200, c_res.text

        other_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": other_doc_email,
                "password": fixtures["password"],
            },
        )
        assert other_login.status_code == 200
        other_token = other_login.json()["accessToken"]

        # Other clinic doctor routes nasal obstruction -> gets system template (42 days), not Clinic 1's override (99 days)
        other_route_res = await client.post(
            "/api/v1/encounter-templates/route",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"complaintCodes": ["CC.NASAL_OBSTRUCTION"]},
        )
        assert other_route_res.status_code == 200
        assert other_route_res.json()["scope"] == "system"
        assert other_route_res.json()["config"]["defaultFollowUpDays"] == 42
