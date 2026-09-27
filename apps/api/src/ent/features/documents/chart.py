"""Assemble the live chart values a patient summary freezes at finalization."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import ValidationError
from ent.core.security.principal import CurrentUser
from ent.features.documents.snapshot import (
    active_allergy_ids,
    active_flag_codes,
    active_medication_names,
    active_problem_ids,
    summary_data,
)
from ent.features.documents.support import concept_displays, utcnow
from ent.features.patients.repository import (
    PatientAllergyRepository,
    PatientFlagRepository,
    PatientMedicationRepository,
    PatientProblemRepository,
    PatientRepository,
)


async def load_summary_data(
    session: AsyncSession,
    user: CurrentUser,
    *,
    patient: Any,
    clinic: Any,
    locale: str,
) -> dict[str, Any]:
    clinic_id = user.clinic_id
    patient_id = int(patient.id)
    allergies = await PatientAllergyRepository(
        session, clinic_id=clinic_id
    ).list_for_patient(patient_id)
    problems = await PatientProblemRepository(
        session, clinic_id=clinic_id
    ).list_for_patient(patient_id)
    medications = await PatientMedicationRepository(
        session, clinic_id=clinic_id
    ).list_for_patient(patient_id)
    flags = await PatientFlagRepository(session, clinic_id=clinic_id).list_for_patient(
        patient_id
    )
    concept_ids = set(active_allergy_ids(allergies)) | set(active_problem_ids(problems))
    labels = await PatientRepository(session, clinic_id=clinic_id).concept_labels(
        concept_ids,
        locale=locale,
        clinic_default_locale=clinic.default_locale,
    )
    try:
        return summary_data(
            patient=patient,
            clinic=clinic,
            on_date=utcnow().date(),
            allergies=concept_displays(labels, active_allergy_ids(allergies)),
            problems=concept_displays(labels, active_problem_ids(problems)),
            medications=active_medication_names(medications),
            safety_alerts=active_flag_codes(flags),
        )
    except ValueError as exc:
        raise ValidationError(reason="birth_date") from exc
