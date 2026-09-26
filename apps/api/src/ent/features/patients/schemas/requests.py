"""Patient write models."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import Field, model_validator

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality

Sex = Literal["male", "female", "other", "unknown"]
IdentifierType = Literal["national_id", "passport", "insurance"]
AllergyCategory = Literal["drug", "food", "other"]
AllergySeverity = Literal["mild", "moderate", "severe"]
MedicationSource = Literal["prescribed_here", "reported", "external"]
FlagCode = Literal[
    "only_hearing_ear",
    "anticoagulant",
    "ototoxic_therapy",
    "difficult_airway",
    "tracheostomy",
    "laryngeal_stenosis",
    "cochlear_implant",
    "pacemaker",
    "immunosuppressed",
    "diabetes",
    "pregnancy",
    "breastfeeding",
    "pediatric_weight_missing",
]
ProblemStatus = Literal["active", "resolved", "suspected", "ruled_out"]
HistoryCategory = Literal[
    "ent_surgery",
    "other_surgery",
    "medical",
    "family",
    "social",
    "obstetric",
]


class PatientIdentifierCreate(CamelModel):
    type: IdentifierType
    value: str = Field(min_length=1, max_length=80)
    issuing_country: str | None = Field(default=None, min_length=2, max_length=2)


class PatientIdentifierUpdate(CamelModel):
    version: int = Field(ge=1)
    value: str | None = Field(default=None, min_length=1, max_length=80)
    issuing_country: str | None = Field(default=None, min_length=2, max_length=2)


class PatientAllergyCreate(CamelModel):
    substance_concept_id: str = Field(min_length=26, max_length=26)
    category: AllergyCategory
    reaction_concept_id: str | None = Field(default=None, min_length=26, max_length=26)
    severity: AllergySeverity | None = None
    onset_date: date | None = None
    is_active: bool = True
    note: str | None = None


class PatientAllergyUpdate(CamelModel):
    version: int = Field(ge=1)
    category: AllergyCategory | None = None
    reaction_concept_id: str | None = Field(default=None, min_length=26, max_length=26)
    severity: AllergySeverity | None = None
    onset_date: date | None = None
    is_active: bool | None = None
    note: str | None = None


class PatientMedicationCreate(CamelModel):
    free_text_name: str = Field(min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=60)
    frequency: str | None = Field(default=None, max_length=60)
    route: str | None = Field(default=None, max_length=30)
    started_on: date | None = None
    stopped_on: date | None = None
    is_active: bool = True
    is_anticoagulant: bool = False
    is_ototoxic: bool = False
    source: MedicationSource


class PatientMedicationUpdate(CamelModel):
    version: int = Field(ge=1)
    free_text_name: str | None = Field(default=None, min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=60)
    frequency: str | None = Field(default=None, max_length=60)
    route: str | None = Field(default=None, max_length=30)
    started_on: date | None = None
    stopped_on: date | None = None
    is_active: bool | None = None
    is_anticoagulant: bool | None = None
    is_ototoxic: bool | None = None
    source: MedicationSource | None = None


class PatientFlagCreate(CamelModel):
    flag_code: FlagCode
    laterality: Laterality | None = None
    severity: str | None = Field(default=None, max_length=20)
    detail: dict[str, Any] | None = None
    started_on: date
    ended_on: date | None = None
    is_auto: bool = False

    @model_validator(mode="after")
    def end_not_before_start(self) -> PatientFlagCreate:
        if self.ended_on is not None and self.ended_on < self.started_on:
            msg = "ended_on_before_started_on"
            raise ValueError(msg)
        return self


class PatientFlagUpdate(CamelModel):
    version: int = Field(ge=1)
    laterality: Laterality | None = None
    severity: str | None = Field(default=None, max_length=20)
    detail: dict[str, Any] | None = None
    started_on: date | None = None
    ended_on: date | None = None
    is_auto: bool | None = None


class PatientProblemCreate(CamelModel):
    diagnosis_concept_id: str = Field(min_length=26, max_length=26)
    laterality: Laterality
    status: ProblemStatus
    onset_date: date | None = None
    resolved_date: date | None = None
    note: str | None = None


class PatientProblemUpdate(CamelModel):
    version: int = Field(ge=1)
    laterality: Laterality | None = None
    status: ProblemStatus | None = None
    onset_date: date | None = None
    resolved_date: date | None = None
    note: str | None = None


class PatientHistoryCreate(CamelModel):
    category: HistoryCategory
    concept_id: str | None = Field(default=None, min_length=26, max_length=26)
    free_text: str | None = Field(default=None, max_length=400)
    laterality: Laterality | None = None
    occurred_year: int | None = Field(default=None, ge=1900, le=2100)
    occurred_date: date | None = None
    detail: dict[str, Any] | None = None

    @model_validator(mode="after")
    def requires_concept_or_text(self) -> PatientHistoryCreate:
        if self.concept_id is None and not (self.free_text and self.free_text.strip()):
            msg = "history_requires_concept_or_text"
            raise ValueError(msg)
        return self


class PatientHistoryUpdate(CamelModel):
    version: int = Field(ge=1)
    concept_id: str | None = Field(default=None, min_length=26, max_length=26)
    free_text: str | None = Field(default=None, max_length=400)
    laterality: Laterality | None = None
    occurred_year: int | None = Field(default=None, ge=1900, le=2100)
    occurred_date: date | None = None
    detail: dict[str, Any] | None = None


class PatientCreate(CamelModel):
    mrn: str | None = Field(default=None, min_length=1, max_length=32)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    first_name_alt: str | None = Field(default=None, max_length=80)
    last_name_alt: str | None = Field(default=None, max_length=80)
    birth_date: date
    birth_date_is_estimated: bool = False
    sex: Sex
    preferred_locale: str = Field(min_length=2, max_length=10)
    phone_primary: str | None = Field(default=None, max_length=32)
    phone_secondary: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=190)
    address_line1: str | None = Field(default=None, max_length=160)
    address_line2: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    occupation: str | None = Field(default=None, max_length=120)
    noise_exposure: str | None = Field(default=None, max_length=40)
    smoking_status: str | None = Field(default=None, max_length=30)
    alcohol_status: str | None = Field(default=None, max_length=30)
    insurance_number: str | None = Field(default=None, max_length=60)
    referring_doctor_name: str | None = Field(default=None, max_length=160)
    referring_doctor_phone: str | None = Field(default=None, max_length=32)
    referring_doctor_email: str | None = Field(default=None, max_length=190)
    referring_doctor_locale: str | None = Field(default=None, max_length=10)
    guardian_name: str | None = Field(default=None, max_length=160)
    guardian_relation: str | None = Field(default=None, max_length=40)
    emergency_contact_name: str | None = Field(default=None, max_length=160)
    emergency_contact_phone: str | None = Field(default=None, max_length=32)
    consent_sms: bool = False
    consent_email: bool = False
    consent_teaching: bool = False
    is_deceased: bool = False
    deceased_date: date | None = None
    confirm_duplicate: bool = False
    identifiers: list[PatientIdentifierCreate] = Field(default_factory=list)
    allergies: list[PatientAllergyCreate] = Field(default_factory=list)
    medications: list[PatientMedicationCreate] = Field(default_factory=list)
    flags: list[PatientFlagCreate] = Field(default_factory=list)
    problems: list[PatientProblemCreate] = Field(default_factory=list)
    history: list[PatientHistoryCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def deceased_date_consistent(self) -> PatientCreate:
        if self.deceased_date is not None and not self.is_deceased:
            msg = "deceased_date_requires_is_deceased"
            raise ValueError(msg)
        if self.deceased_date is not None and self.deceased_date < self.birth_date:
            msg = "deceased_date_before_birth_date"
            raise ValueError(msg)
        if self.birth_date > date.today():
            msg = "birth_date_in_future"
            raise ValueError(msg)
        return self


class PatientUpdate(CamelModel):
    version: int = Field(ge=1)
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    first_name_alt: str | None = Field(default=None, max_length=80)
    last_name_alt: str | None = Field(default=None, max_length=80)
    birth_date: date | None = None
    birth_date_is_estimated: bool | None = None
    sex: Sex | None = None
    preferred_locale: str | None = Field(default=None, min_length=2, max_length=10)
    phone_primary: str | None = Field(default=None, max_length=32)
    phone_secondary: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=190)
    address_line1: str | None = Field(default=None, max_length=160)
    address_line2: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    occupation: str | None = Field(default=None, max_length=120)
    noise_exposure: str | None = Field(default=None, max_length=40)
    smoking_status: str | None = Field(default=None, max_length=30)
    alcohol_status: str | None = Field(default=None, max_length=30)
    insurance_number: str | None = Field(default=None, max_length=60)
    referring_doctor_name: str | None = Field(default=None, max_length=160)
    referring_doctor_phone: str | None = Field(default=None, max_length=32)
    referring_doctor_email: str | None = Field(default=None, max_length=190)
    referring_doctor_locale: str | None = Field(default=None, max_length=10)
    guardian_name: str | None = Field(default=None, max_length=160)
    guardian_relation: str | None = Field(default=None, max_length=40)
    emergency_contact_name: str | None = Field(default=None, max_length=160)
    emergency_contact_phone: str | None = Field(default=None, max_length=32)
    consent_sms: bool | None = None
    consent_email: bool | None = None
    consent_teaching: bool | None = None
    is_deceased: bool | None = None
    deceased_date: date | None = None


class PatientMergeRequest(CamelModel):
    merged_patient_id: str = Field(min_length=26, max_length=26)
    reason: str = Field(min_length=1, max_length=2000)
