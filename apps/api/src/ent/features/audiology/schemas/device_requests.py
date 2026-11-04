"""P4-06 request schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ent.core.schemas.base import CamelModel
from ent.features.audiology.constants import (
    HEARING_DEVICE_TYPES,
)

HearingDeviceEar = Literal["right", "left"]
HearingDeviceType = Literal[
    "bte",
    "ric",
    "ite",
    "cros",
    "bone_conduction",
    "cochlear_implant",
    "middle_ear_implant",
]
HearingDeviceStatus = Literal["active", "trial", "inactive", "replaced", "removed"]
ScreenResult = Literal["pass", "refer", "not_tested"]
DiagnosticAbrResult = Literal["normal", "elevated", "absent", "not_tested"]
InterventionType = Literal[
    "hearing_aid",
    "cochlear_implant",
    "speech_therapy",
    "early_intervention",
    "monitoring",
]
OmeStatus = Literal[
    "watchful_waiting",
    "resolved",
    "persisted_tubes_proposed",
    "tubes_inserted",
]
CandidacyKind = Literal["hearing_aid", "cochlear_implant"]
OmeLaterality = Literal["right", "left", "bilateral"]


class AidedThresholdInput(CamelModel):
    frequency_hz: int = Field(ge=125, le=16000)
    level_db: int = Field(ge=-10, le=130)


class HearingDeviceCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    ear: HearingDeviceEar
    device_type: HearingDeviceType
    brand: str | None = Field(default=None, max_length=60)
    model: str | None = Field(default=None, max_length=60)
    serial: str | None = Field(default=None, max_length=60)
    fitted_on: date | None = None
    fitted_by: str | None = Field(default=None, max_length=120)
    warranty_end: date | None = None
    last_programmed_on: date | None = None
    battery_type: str | None = Field(default=None, max_length=40)
    daily_use_hours: Decimal | None = Field(default=None, ge=0, le=24)
    satisfaction: int | None = Field(default=None, ge=0, le=10)
    status: HearingDeviceStatus = "active"
    aided_thresholds: list[AidedThresholdInput] | None = None
    surgeon: str | None = Field(default=None, max_length=120)
    surgery_date: date | None = None
    electrode_array: str | None = Field(default=None, max_length=80)
    implant_activation_date: date | None = None
    mapping_dates: list[date] | None = None
    complications: str | None = Field(default=None, max_length=255)
    mri_conditions: str | None = Field(default=None, max_length=160)
    notes: str | None = None

    @field_validator("device_type")
    @classmethod
    def device_type_allowed(cls, value: str) -> str:
        if value not in HEARING_DEVICE_TYPES:
            msg = "device_type"
            raise ValueError(msg)
        return value


class HearingDeviceUpdate(CamelModel):
    version: int = Field(ge=1)
    brand: str | None = Field(default=None, max_length=60)
    model: str | None = Field(default=None, max_length=60)
    serial: str | None = Field(default=None, max_length=60)
    fitted_on: date | None = None
    fitted_by: str | None = Field(default=None, max_length=120)
    warranty_end: date | None = None
    last_programmed_on: date | None = None
    battery_type: str | None = Field(default=None, max_length=40)
    daily_use_hours: Decimal | None = Field(default=None, ge=0, le=24)
    satisfaction: int | None = Field(default=None, ge=0, le=10)
    status: HearingDeviceStatus | None = None
    aided_thresholds: list[AidedThresholdInput] | None = None
    surgeon: str | None = Field(default=None, max_length=120)
    surgery_date: date | None = None
    electrode_array: str | None = Field(default=None, max_length=80)
    implant_activation_date: date | None = None
    mapping_dates: list[date] | None = None
    complications: str | None = Field(default=None, max_length=255)
    mri_conditions: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class CandidacyEvaluate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    audiogram_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    hearing_aid_trial_completed: bool = False
    imaging_clearance: bool = False
    communication_impact_assessed: bool = False


class CandidacyConfirm(CamelModel):
    kind: CandidacyKind
    audiogram_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    hearing_aid_trial_completed: bool = False
    imaging_clearance: bool = False
    communication_impact_assessed: bool = False


class NewbornScreeningUpdate(CamelModel):
    screen_date: date | None = None
    screen_result_right: ScreenResult | None = None
    screen_result_left: ScreenResult | None = None
    rescreen_date: date | None = None
    rescreen_result_right: ScreenResult | None = None
    rescreen_result_left: ScreenResult | None = None
    diagnostic_abr_date: date | None = None
    diagnostic_abr_result_right: DiagnosticAbrResult | None = None
    diagnostic_abr_result_left: DiagnosticAbrResult | None = None
    permanent_hearing_loss: bool | None = None
    intervention_date: date | None = None
    intervention_type: InterventionType | None = None


class MilestonesUpdate(CamelModel):
    milestones: dict[str, bool]


class OmeEpisodeCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    audiogram_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    tympanometry_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    laterality: OmeLaterality
    first_seen_on: date
    hearing_level_db: Decimal | None = Field(default=None, ge=-10, le=130)
    watchful_waiting_start_on: date | None = None
    notes: str | None = None


class OmeEpisodeUpdate(CamelModel):
    version: int = Field(ge=1)
    status: OmeStatus | None = None
    resolved_on: date | None = None
    hearing_level_db: Decimal | None = Field(default=None, ge=-10, le=130)
    notes: str | None = None

    @model_validator(mode="after")
    def resolved_requires_date(self) -> OmeEpisodeUpdate:
        if self.status == "resolved" and self.resolved_on is None:
            msg = "resolved_on_required"
            raise ValueError(msg)
        return self
