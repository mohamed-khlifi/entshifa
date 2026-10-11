"""Load the visit facts a clinical document freezes into its snapshot."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError
from ent.core.security.principal import CurrentUser
from ent.features.clinics.models import Clinic
from ent.features.documents.assemble import VisitFacts
from ent.features.documents.snapshot import (
    active_allergy_ids,
    active_flag_codes,
    clinic_address,
    person_name,
)
from ent.features.documents.support import concept_displays, utcnow
from ent.features.encounters.models import Encounter
from ent.features.patients.models import Patient
from ent.features.patients.repository import (
    PatientAllergyRepository,
    PatientFlagRepository,
    PatientRepository,
)


async def current_flag_codes(
    session: AsyncSession,
    user: CurrentUser,
    patient_id: int,
) -> tuple[str, ...]:
    flags = await PatientFlagRepository(
        session, clinic_id=user.clinic_id
    ).list_for_patient(patient_id)
    return tuple(active_flag_codes(flags))


async def load_visit_facts(
    session: AsyncSession,
    user: CurrentUser,
    *,
    patient: Patient,
    clinic: Clinic,
    encounter: Encounter,
    locale: str,
) -> VisitFacts:
    clinic_id = user.clinic_id
    patient_id = int(patient.id)
    if int(encounter.patient_id) != patient_id:
        raise NotFoundError()
    allergies = await PatientAllergyRepository(
        session, clinic_id=clinic_id
    ).list_for_patient(patient_id)
    flags = await PatientFlagRepository(session, clinic_id=clinic_id).list_for_patient(
        patient_id
    )
    complaint_ids = [int(row.concept_id) for row in encounter.complaints]
    diagnosis_ids = [
        int(row.concept_id) for row in encounter.diagnoses if row.status != "ruled_out"
    ]
    concept_ids = (
        set(active_allergy_ids(allergies)) | set(complaint_ids) | set(diagnosis_ids)
    )
    labels = await PatientRepository(session, clinic_id=clinic_id).concept_labels(
        concept_ids,
        locale=locale,
        clinic_default_locale=clinic.default_locale,
    )
    clinician = encounter.clinician
    site_name = encounter.site.name if encounter.site is not None else ""
    return VisitFacts(
        patient_name=person_name(patient.first_name, patient.last_name),
        mrn=patient.mrn,
        birth_date=patient.birth_date.isoformat(),
        sex=patient.sex,
        clinic_name=clinic.name,
        clinic_phone=clinic.phone or "",
        clinic_address=clinic_address(clinic),
        issued_on=utcnow().date().isoformat(),
        encounter_date=encounter.started_at.date().isoformat(),
        clinician_name=person_name(clinician.first_name, clinician.last_name),
        site_name=site_name,
        encounter_type=encounter.encounter_type,
        complaints=tuple(concept_displays(labels, complaint_ids)),
        history=(encounter.history_text or "").strip(),
        diagnoses=tuple(concept_displays(labels, diagnosis_ids)),
        assessment=(encounter.assessment_text or "").strip(),
        plan=(encounter.plan_text or "").strip(),
        referring_doctor_name=(patient.referring_doctor_name or "").strip(),
        referring_doctor_locale=patient.referring_doctor_locale,
        preferred_locale=patient.preferred_locale,
        clinic_default_locale=clinic.default_locale,
        flag_codes=tuple(active_flag_codes(flags)),
        allergy_labels=tuple(concept_displays(labels, active_allergy_ids(allergies))),
    )
