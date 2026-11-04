"""P4-06 response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ent.core.schemas.base import CamelModel
from ent.features.audiology.schemas.device_requests import (
    CandidacyKind,
    DiagnosticAbrResult,
    HearingDeviceEar,
    HearingDeviceStatus,
    HearingDeviceType,
    InterventionType,
    OmeLaterality,
    OmeStatus,
    ScreenResult,
)


class AidedThresholdRead(CamelModel):
    frequency_hz: int
    level_db: int


class HearingDeviceRead(CamelModel):
    public_id: str
    patient_public_id: str
    ear: HearingDeviceEar
    device_type: HearingDeviceType
    brand: str | None
    model: str | None
    serial: str | None
    fitted_on: date | None
    fitted_by: str | None
    warranty_end: date | None
    last_programmed_on: date | None
    battery_type: str | None
    daily_use_hours: float | None
    satisfaction: int | None
    status: HearingDeviceStatus
    aided_thresholds: list[AidedThresholdRead] | None
    surgeon: str | None
    surgery_date: date | None
    electrode_array: str | None
    implant_activation_date: date | None
    mapping_dates: list[date] | None
    complications: str | None
    mri_conditions: str | None
    notes: str | None
    version: int


class ChecklistItemRead(CamelModel):
    code: str
    met: bool


class CandidacyEvaluationRead(CamelModel):
    hearing_aid_items: list[ChecklistItemRead]
    cochlear_implant_items: list[ChecklistItemRead]
    hearing_aid_eligible: bool
    cochlear_implant_eligible: bool
    engine_version: str
    engine_reference: str


class CandidacyConfirmationRead(CamelModel):
    kind: CandidacyKind
    confirmed_at: datetime
    confirmed_by_public_id: str
    evaluation: CandidacyEvaluationRead


class PediatricAudiologyRead(CamelModel):
    public_id: str
    patient_public_id: str
    screen_date: date | None
    screen_result_right: ScreenResult | None
    screen_result_left: ScreenResult | None
    rescreen_date: date | None
    rescreen_result_right: ScreenResult | None
    rescreen_result_left: ScreenResult | None
    diagnostic_abr_date: date | None
    diagnostic_abr_result_right: DiagnosticAbrResult | None
    diagnostic_abr_result_left: DiagnosticAbrResult | None
    permanent_hearing_loss: bool
    intervention_date: date | None
    intervention_type: InterventionType | None
    screen_by_1m_status: str
    diagnosis_by_3m_status: str
    intervention_by_6m_status: str
    ehdi_engine_version: str | None
    speech_language_milestones: dict[str, bool] | None
    candidacy_snapshot: dict[str, Any] | None
    ha_candidacy_confirmed_at: datetime | None
    ha_candidacy_confirmed_by_public_id: str | None
    ci_candidacy_confirmed_at: datetime | None
    ci_candidacy_confirmed_by_public_id: str | None
    version: int


class OmeEpisodeRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    audiogram_public_id: str | None
    tympanometry_public_id: str | None
    laterality: OmeLaterality
    first_seen_on: date
    hearing_level_db: float | None
    watchful_waiting_start_on: date
    watchful_waiting_due_on: date
    status: OmeStatus
    resolved_on: date | None
    notes: str | None
    version: int


class PediatricSummaryRead(CamelModel):
    pediatric: PediatricAudiologyRead | None
    ome_episodes: list[OmeEpisodeRead]
