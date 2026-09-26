"""Patient read models. Integer ids never leave the process."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class PatientIdentifierRead(CamelModel):
    public_id: str
    type: str
    value: str
    issuing_country: str | None
    version: int


class PatientAllergyRead(CamelModel):
    public_id: str
    substance: CodeableConcept
    category: str
    reaction: CodeableConcept | None
    severity: str | None
    onset_date: date | None
    is_active: bool
    note: str | None
    version: int


class PatientMedicationRead(CamelModel):
    public_id: str
    free_text_name: str | None
    dose: str | None
    frequency: str | None
    route: str | None
    started_on: date | None
    stopped_on: date | None
    is_active: bool
    is_anticoagulant: bool
    is_ototoxic: bool
    source: str
    version: int


class PatientFlagRead(CamelModel):
    public_id: str
    flag_code: str
    laterality: str | None
    severity: str | None
    detail: dict[str, Any] | None
    started_on: date
    ended_on: date | None
    is_auto: bool
    recorded_by_public_id: str | None
    version: int


class PatientProblemRead(CamelModel):
    public_id: str
    diagnosis: CodeableConcept
    laterality: str
    status: str
    onset_date: date | None
    resolved_date: date | None
    note: str | None
    version: int


class PatientHistoryRead(CamelModel):
    public_id: str
    category: str
    concept: CodeableConcept | None
    free_text: str | None
    laterality: str | None
    occurred_year: int | None
    occurred_date: date | None
    detail: dict[str, Any] | None
    version: int


class PatientSummaryRead(CamelModel):
    public_id: str
    mrn: str
    first_name: str
    last_name: str
    first_name_alt: str | None
    last_name_alt: str | None
    birth_date: date
    birth_date_is_estimated: bool
    sex: str
    preferred_locale: str
    phone_primary: str | None
    version: int


class PatientRead(PatientSummaryRead):
    phone_secondary: str | None
    email: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    postal_code: str | None
    country_code: str | None
    occupation: str | None
    noise_exposure: str | None
    smoking_status: str | None
    alcohol_status: str | None
    insurance_number: str | None
    referring_doctor_name: str | None
    referring_doctor_phone: str | None
    referring_doctor_email: str | None
    referring_doctor_locale: str | None
    guardian_name: str | None
    guardian_relation: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    consent_sms: bool
    consent_email: bool
    consent_teaching: bool
    is_deceased: bool
    deceased_date: date | None
    created_at: datetime
    updated_at: datetime
    identifiers: list[PatientIdentifierRead]
    allergies: list[PatientAllergyRead]
    medications: list[PatientMedicationRead]
    flags: list[PatientFlagRead]
    problems: list[PatientProblemRead]
    history: list[PatientHistoryRead]


class PatientMergeRead(CamelModel):
    surviving_patient_id: str
    merged_patient_id: str
    merge_log_public_id: str
