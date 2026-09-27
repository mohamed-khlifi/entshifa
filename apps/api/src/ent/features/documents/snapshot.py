"""Chart fields frozen into a patient-summary snapshot."""

from __future__ import annotations

from datetime import date

from ent.engines.documents.age import completed_age
from ent.features.clinics.models import Clinic
from ent.features.patients.models import (
    Patient,
    PatientAllergy,
    PatientFlag,
    PatientMedication,
    PatientProblem,
)


def person_name(first_name: str, last_name: str) -> str:
    return " ".join(part.strip() for part in (first_name, last_name) if part.strip())


def clinic_address(clinic: Clinic) -> str:
    parts = (
        clinic.address_line1,
        clinic.address_line2,
        clinic.postal_code,
        clinic.city,
    )
    return ", ".join(part.strip() for part in parts if part and part.strip())


def summary_data(
    *,
    patient: Patient,
    clinic: Clinic,
    on_date: date,
    allergies: list[str],
    problems: list[str],
    medications: list[str],
    safety_alerts: list[str],
) -> dict[str, object]:
    years, months = completed_age(patient.birth_date, on_date)
    alt = person_name(patient.first_name_alt or "", patient.last_name_alt or "")
    return {
        "patient": {
            "fullName": person_name(patient.first_name, patient.last_name),
            "fullNameAlt": alt,
            "mrn": patient.mrn,
            "birthDate": patient.birth_date.isoformat(),
            "ageYears": years,
            "ageMonths": months,
            "sex": patient.sex,
            "safetyAlerts": safety_alerts,
            "allergies": allergies,
            "problems": problems,
            "medications": medications,
        },
        "clinic": {
            "name": clinic.name,
            "phone": clinic.phone or "",
            "address": clinic_address(clinic),
        },
        "document": {"issuedOn": on_date.isoformat()},
    }


def active_allergy_ids(rows: list[PatientAllergy]) -> list[int]:
    return [int(row.substance_concept_id) for row in rows if row.is_active]


def active_problem_ids(rows: list[PatientProblem]) -> list[int]:
    return [int(row.diagnosis_concept_id) for row in rows if row.status == "active"]


def active_medication_names(rows: list[PatientMedication]) -> list[str]:
    names: list[str] = []
    for row in rows:
        if not row.is_active:
            continue
        if row.free_text_name and row.free_text_name.strip():
            names.append(row.free_text_name.strip())
    return names


def active_flag_codes(rows: list[PatientFlag]) -> list[str]:
    return [row.flag_code for row in rows if row.ended_on is None]
