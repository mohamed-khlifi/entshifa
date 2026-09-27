"""Demo patients loaded from ``dev-seed-data.json`` at the repository root."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.principal import CurrentUser
from ent.features.auth.repository import AuthRepository
from ent.features.patients.models import Patient
from ent.features.patients.schemas.requests import (
    PatientCreate,
    PatientFlagCreate,
    PatientHistoryCreate,
    PatientMedicationCreate,
    PatientProblemCreate,
)
from ent.features.patients.service import PatientService
from ent.features.terminology.models import Concept
from ent.seeds.paths import dev_seed_input_path

_DEFAULT_CREATOR = "doctor1@demo.entshifa.local"
_DEMO_MRN_PREFIX = "DEMO-"


async def _concept_public_id(session: AsyncSession, code: str) -> str | None:
    value = (
        await session.execute(
            select(Concept.public_id).where(
                Concept.code == code,
                Concept.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    return str(value) if value is not None else None


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


async def _build_patient_create(
    session: AsyncSession,
    raw: dict[str, Any],
) -> PatientCreate:
    medications: list[PatientMedicationCreate] = []
    for row in raw.get("medications", []):
        medications.append(
            PatientMedicationCreate(
                free_text_name=row["freeTextName"],
                dose=row.get("dose"),
                frequency=row.get("frequency"),
                route=row.get("route"),
                is_active=row.get("isActive", True),
                is_anticoagulant=row.get("isAnticoagulant", False),
                is_ototoxic=row.get("isOtotoxic", False),
                source=row["source"],
            ),
        )

    problems: list[PatientProblemCreate] = []
    for row in raw.get("problems", []):
        concept_code = row["diagnosisConceptCode"]
        public_id = await _concept_public_id(session, concept_code)
        if public_id is None:
            msg = f"Unknown concept code in dev seed: {concept_code}"
            raise RuntimeError(msg)
        problems.append(
            PatientProblemCreate(
                diagnosis_concept_id=public_id,
                laterality=row.get("laterality", "na"),
                status=row["status"],
                onset_date=(
                    _parse_date(row["onsetDate"]) if row.get("onsetDate") else None
                ),
                note=row.get("note"),
            ),
        )

    flags: list[PatientFlagCreate] = []
    for row in raw.get("flags", []):
        flags.append(
            PatientFlagCreate(
                flag_code=row["flagCode"],
                laterality=row.get("laterality"),
                started_on=_parse_date(row["startedOn"]),
                ended_on=(
                    _parse_date(row["endedOn"]) if row.get("endedOn") else None
                ),
                is_auto=row.get("isAuto", False),
            ),
        )

    history: list[PatientHistoryCreate] = []
    for row in raw.get("history", []):
        concept_id = None
        if code := row.get("conceptCode"):
            concept_id = await _concept_public_id(session, code)
        history.append(
            PatientHistoryCreate(
                category=row["category"],
                concept_id=concept_id,
                free_text=row.get("freeText"),
                laterality=row.get("laterality"),
                occurred_year=row.get("occurredYear"),
                occurred_date=(
                    _parse_date(row["occurredDate"])
                    if row.get("occurredDate")
                    else None
                ),
            ),
        )

    return PatientCreate(
        mrn=raw.get("mrn"),
        first_name=raw["firstName"],
        last_name=raw["lastName"],
        first_name_alt=raw.get("firstNameAlt"),
        last_name_alt=raw.get("lastNameAlt"),
        birth_date=_parse_date(raw["birthDate"]),
        birth_date_is_estimated=raw.get("birthDateIsEstimated", False),
        sex=raw["sex"],
        preferred_locale=raw.get("preferredLocale", "fr"),
        phone_primary=raw.get("phonePrimary"),
        phone_secondary=raw.get("phoneSecondary"),
        email=raw.get("email"),
        city=raw.get("city"),
        country_code=raw.get("countryCode"),
        guardian_name=raw.get("guardianName"),
        guardian_relation=raw.get("guardianRelation"),
        noise_exposure=raw.get("noiseExposure"),
        smoking_status=raw.get("smokingStatus"),
        alcohol_status=raw.get("alcoholStatus"),
        is_deceased=raw.get("isDeceased", False),
        confirm_duplicate=True,
        medications=medications,
        problems=problems,
        flags=flags,
        history=history,
    )


async def _seed_actor(
    session: AsyncSession,
    *,
    clinic_id: int,
    clinic_public_id: str,
    creator_email: str,
) -> CurrentUser | None:
    repo = AuthRepository(session)
    user = await repo.get_user_by_email(creator_email)
    if user is None:
        return None
    permissions = await repo.load_permission_codes(user.id, clinic_id)
    return CurrentUser(
        user_id=user.id,
        user_public_id=user.public_id,
        session_id=0,
        session_public_id="00000000000000000000000000",
        clinic_id=clinic_id,
        clinic_public_id=clinic_public_id,
        permissions=permissions,
    )


async def seed_dev_patients(
    session: AsyncSession,
    *,
    clinic_id: int,
    clinic_public_id: str,
    creator_email: str = _DEFAULT_CREATOR,
) -> int:
    path = dev_seed_input_path()
    if not path.is_file():
        return 0

    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = payload.get("patients", [])
    if not rows:
        return 0

    actor = await _seed_actor(
        session,
        clinic_id=clinic_id,
        clinic_public_id=clinic_public_id,
        creator_email=creator_email,
    )
    if actor is None:
        return 0

    service = PatientService(session)
    created = 0
    for raw in rows:
        mrn = raw.get("mrn")
        if mrn:
            exists = (
                await session.execute(
                    select(Patient.id).where(
                        Patient.clinic_id == clinic_id,
                        Patient.mrn == mrn,
                        Patient.deleted_at.is_(None),
                    ),
                )
            ).scalar_one_or_none()
            if exists is not None:
                continue

        body = await _build_patient_create(session, raw)
        await service.create_patient(
            user=actor,
            body=body,
            idempotency_key=None,
            content_locale=body.preferred_locale,
        )
        created += 1

    return created
