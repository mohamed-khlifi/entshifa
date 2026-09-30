"""Cross-tenant isolation over every registered tenant route (P1-11)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from ent.core.context import set_clinic_id, set_request_id, set_user_id
from ent.core.db.session import get_session_factory
from ent.core.utils.ids import new_ulid
from ent.engines.patients.name_normalize import build_name_normalized
from ent.features.attachments.models import Attachment
from ent.features.clinics.models import Clinic, Site
from ent.features.documents.models import (
    Document,
    DocumentTemplate,
    DocumentTemplateVersion,
)
from ent.features.encounters.models import Encounter
from ent.features.observations.models import Observation
from ent.features.patients.models import (
    Patient,
    PatientAllergy,
    PatientFlag,
    PatientHistory,
    PatientIdentifier,
    PatientMedication,
    PatientProblem,
)
from ent.features.scheduling.models import Appointment, AppointmentType
from ent.features.terminology.models import CodeSystem, Concept
from ent.features.users.models import User
from ent.main import create_app
from ent.seeds.identity import ensure_role, ensure_user_with_role
from ent.seeds.terminology import seed_terminology
from ent.settings import get_settings
from tests.api.cross_tenant_catalog import (
    COLLECTION_ROUTES,
    MUTATION_OK,
    QUERY_TENANT_ROUTES,
    classify_route,
    fill_path,
    iter_api_routes,
)
from tests.support.clinic_seed import seed_clinic_admin_fixtures


def _forbidden(text: str, needles: list[str]) -> str | None:
    for needle in needles:
        if needle and needle in text:
            return needle
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_registered_routes_do_not_leak_across_tenants() -> None:
    app = create_app(settings=get_settings())
    factory = get_session_factory()
    token = new_ulid()
    last_name = f"Tenant{token[:6]}"
    concept_code = f"XT.{token[:8]}"
    room = f"room-{token[:10].lower()}"
    starts = datetime(2026, 6, 15, 10, 0, 0)
    async with factory() as session:
        try:
            fixtures = await seed_clinic_admin_fixtures(session)
            await seed_terminology(session)
        except Exception as exc:
            pytest.skip(f"Database not ready: {exc}")

        other = (
            await session.execute(
                select(Clinic).where(
                    Clinic.public_id == fixtures["other_clinic_public_id"]
                ),
            )
        ).scalar_one()
        site = (
            await session.execute(
                select(Site).where(Site.public_id == fixtures["other_site_public_id"]),
            )
        ).scalar_one()
        set_request_id(new_ulid())
        set_clinic_id(other.id)
        set_user_id(None)
        role = await ensure_role(
            session,
            clinic=other,
            code="doctor",
            name_key="role.doctor",
        )
        other_email = f"foreign-{token[:8].lower()}@test.entshifa.local"
        seeded_user = await ensure_user_with_role(
            session,
            clinic=other,
            role=role,
            email=other_email,
            first_name="Foreign",
            last_name="Doctor",
        )
        other_user = (
            await session.execute(select(User).where(User.email == other_email))
        ).scalar_one()
        system = (await session.execute(select(CodeSystem).limit(1))).scalar_one()
        substance = (await session.execute(select(Concept).limit(1))).scalar_one()
        concept = Concept(
            public_id=new_ulid(),
            code_system_id=system.id,
            code=concept_code,
            kind="finding",
            clinic_id=other.id,
            sort_order=0,
        )
        session.add(concept)
        patient = Patient(
            public_id=new_ulid(),
            clinic_id=other.id,
            mrn=f"XT{token[:10]}",
            first_name="Foreign",
            last_name=last_name,
            name_normalized=build_name_normalized(
                first_name="Foreign", last_name=last_name
            ),
            birth_date=datetime(1975, 6, 1).date(),
            sex="female",
            preferred_locale="en",
            email=f"patient-{token[:8].lower()}@example.local",
        )
        session.add(patient)
        await session.flush()
        identifier = PatientIdentifier(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            type="national_id",
            value=f"NID{token[:8]}",
        )
        allergy = PatientAllergy(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            substance_concept_id=substance.id,
            category="drug",
        )
        medication = PatientMedication(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            source="reported",
            free_text_name="secret drug",
        )
        flag = PatientFlag(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            flag_code="pacemaker",
            started_on=datetime(2020, 1, 1).date(),
        )
        problem = PatientProblem(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            diagnosis_concept_id=substance.id,
            laterality="na",
            status="active",
        )
        history = PatientHistory(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            category="medical",
            free_text="secret history",
        )
        appointment_type = AppointmentType(
            public_id=new_ulid(),
            clinic_id=other.id,
            code=f"xt{token[:6].lower()}",
            name_key="scheduling.type.crossTenant",
            default_duration_min=20,
            color="#112233",
        )
        template = DocumentTemplate(
            public_id=new_ulid(),
            clinic_id=other.id,
            code=f"xtpl{token[:6].lower()}",
            category="consultation_report",
            placeholders={},
            is_system=False,
            is_active=True,
        )
        attachment = Attachment(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            category="clinical_photo",
            storage_key=f"clinics/{other.id}/secret-{token}",
            filename="secret.jpg",
            content_type="image/jpeg",
            size_bytes=12,
            patient_public_id=patient.public_id,
        )
        session.add_all(
            [
                identifier,
                allergy,
                medication,
                flag,
                problem,
                history,
                appointment_type,
                template,
                attachment,
            ]
        )
        await session.flush()
        version = DocumentTemplateVersion(
            public_id=new_ulid(),
            clinic_id=other.id,
            document_template_id=template.id,
            version=1,
            locale="en",
            direction="ltr",
            header_html="<p>secret</p>",
            body_html="<p>secret</p>",
            footer_html="<p>secret</p>",
            css="",
            page_setup={},
        )
        session.add(version)
        await session.flush()
        document = Document(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            template_id=template.id,
            template_version_id=version.id,
            category="consultation_report",
            locale="en",
            title="Secret letter",
            status="draft",
            content_snapshot={"secret": True},
        )
        appointment = Appointment(
            public_id=new_ulid(),
            clinic_id=other.id,
            site_id=site.id,
            patient_id=patient.id,
            user_id=other_user.id,
            appointment_type_id=appointment_type.id,
            starts_at=starts,
            ends_at=starts + timedelta(minutes=20),
            status="arrived",
            room=room,
            reason_text="secret visit",
        )
        session.add_all([document, appointment])
        await session.flush()
        finding = (
            await session.execute(
                select(Concept).where(Concept.code == "FIND.TM.NORMAL")
            )
        ).scalar_one()
        encounter_public_id = new_ulid()
        encounter = Encounter(
            public_id=encounter_public_id,
            clinic_id=other.id,
            site_id=site.id,
            patient_id=patient.id,
            user_id=other_user.id,
            encounter_type="consultation",
            started_at=datetime(2026, 6, 15, 10, 0, 0),
            status="draft",
            history_text="secret history",
            created_by_id=other_user.id,
            updated_by_id=other_user.id,
        )
        session.add(encounter)
        await session.flush()
        observation = Observation(
            public_id=new_ulid(),
            clinic_id=other.id,
            patient_id=patient.id,
            encounter_id=encounter.id,
            encounter_public_id=encounter_public_id,
            concept_id=finding.id,
            laterality="right",
            status="abnormal",
            value_type="ordinal",
            ordinal_value=3,
            effective_at=datetime(2026, 6, 15, 10, 0, 0),
            source="clinician",
            recorded_by_id=other_user.id,
            created_by_id=other_user.id,
            updated_by_id=other_user.id,
        )
        session.add(observation)
        await session.flush()

        ids = {
            "patient_id": patient.public_id,
            "site_id": site.public_id,
            "user_id": seeded_user.public_id,
            "role_id": role.public_id,
            "appointment_id": appointment.public_id,
            "type_id": appointment_type.public_id,
            "document_id": document.public_id,
            "template_id": template.public_id,
            "public_id": attachment.public_id,
            "concept_id": concept.public_id,
            "identifier_id": identifier.public_id,
            "allergy_id": allergy.public_id,
            "medication_id": medication.public_id,
            "flag_id": flag.public_id,
            "problem_id": problem.public_id,
            "history_id": history.public_id,
            "clinic_public_id": other.public_id,
            "encounter_public_id": encounter_public_id,
            "encounter_id": encounter_public_id,
        }
        forbidden = [
            patient.public_id,
            site.public_id,
            seeded_user.public_id,
            role.public_id,
            appointment.public_id,
            appointment_type.public_id,
            document.public_id,
            template.public_id,
            attachment.public_id,
            concept.public_id,
            last_name,
            concept_code,
            room,
            observation.public_id,
            encounter_public_id,
        ]
        await session.commit()

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

        failures: list[str] = []
        for method, path, params in iter_api_routes(app):
            if (method, path) in QUERY_TENANT_ROUTES:
                continue
            if classify_route(method, path, params) != "tenant":
                continue
            url = fill_path(path, ids)
            kwargs: dict[str, object] = {"headers": headers}
            if method in {"POST", "PUT", "PATCH"}:
                kwargs["json"] = {"cancellationReason": "x", "version": 1}
            response = await client.request(method, url, **kwargs)
            if method in {"GET", "DELETE"}:
                if response.status_code != 404:
                    failures.append(
                        f"{method} {path} -> {response.status_code} {response.text[:180]}"
                    )
            elif response.status_code not in MUTATION_OK:
                failures.append(
                    f"{method} {path} -> {response.status_code} {response.text[:180]}"
                )
        assert failures == [], "\n".join(failures)

        for method, path in QUERY_TENANT_ROUTES:
            response = await client.request(
                method,
                path,
                headers=headers,
                params={"patientPublicId": ids["patient_id"]},
            )
            assert response.status_code == 404, response.text

        probes: dict[tuple[str, str], dict[str, str]] = {
            ("GET", "/api/v1/patients"): {"search": last_name, "limit": "100"},
            ("GET", "/api/v1/sites"): {"search": "Other Primary", "limit": "100"},
            ("GET", "/api/v1/users"): {
                "search": other_email.split("@", 1)[0],
                "limit": "100",
            },
            ("GET", "/api/v1/roles"): {},
            ("GET", "/api/v1/appointment-types"): {"limit": "100"},
            ("GET", "/api/v1/appointments"): {
                "startsAfter": "2026-06-01T00:00:00",
                "startsBefore": "2026-07-01T00:00:00",
                "room": room,
                "limit": "100",
            },
            ("GET", "/api/v1/appointments/waiting-room"): {
                "on": "2026-06-15",
                "limit": "100",
            },
            ("GET", "/api/v1/scheduling/doctors"): {"limit": "100"},
            ("GET", "/api/v1/document-templates"): {"limit": "100"},
            ("GET", "/api/v1/auth/clinics"): {},
            ("GET", "/api/v1/terminology/admin/concepts"): {
                "q": concept_code,
                "clinic_owned_only": "true",
                "limit": "100",
            },
            ("GET", "/api/v1/terminology/admin/value-sets"): {},
            ("GET", "/api/v1/terminology/concepts/search"): {
                "q": concept_code,
                "limit": "100",
            },
            ("GET", "/api/v1/observations/cohort"): {
                "conceptCode": "FIND.TM.NORMAL",
                "ordinal": "3",
                "effectiveFrom": "2026-01-01T00:00:00",
                "effectiveTo": "2027-01-01T00:00:00",
                "limit": "100",
            },
        }
        try:
            ZoneInfo("Europe/Paris")
        except ZoneInfoNotFoundError:
            probes.pop(("GET", "/api/v1/appointments/waiting-room"))
        assert set(probes) <= COLLECTION_ROUTES
        leaked: list[str] = []
        for key, params in probes.items():
            method, path = key
            response = await client.request(
                method, path, headers=headers, params=params
            )
            if response.status_code != 200:
                leaked.append(
                    f"{method} {path} -> {response.status_code} {response.text[:180]}"
                )
                continue
            found = _forbidden(response.text, forbidden)
            if found is not None:
                leaked.append(f"{method} {path} leaked {found}")
        assert leaked == [], "\n".join(leaked)
