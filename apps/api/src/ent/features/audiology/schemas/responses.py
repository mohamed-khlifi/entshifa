"""Audiogram API response models."""

from __future__ import annotations

from datetime import date, datetime

from ent.core.schemas.base import CamelModel
from ent.features.audiology.schemas.requests import (
    AudiogramConduction,
    AudiogramEar,
    AudiogramMethod,
    AudiogramReliability,
    AudiogramTransducer,
)


class ThresholdRead(CamelModel):
    ear: AudiogramEar
    conduction: AudiogramConduction
    frequency_hz: int
    level_db: int | None
    is_masked: bool
    is_no_response: bool


class AudiogramRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    performed_at: datetime
    performed_by_public_id: str
    equipment: str | None
    calibration_date: date | None
    transducer: AudiogramTransducer
    method: AudiogramMethod
    reliability: AudiogramReliability
    is_baseline: bool
    baseline_audiogram_public_id: str | None
    pta_formula: str | None
    pta_right: float | None
    pta_left: float | None
    abg_right: float | None
    abg_left: float | None
    grade_right: str | None
    grade_left: str | None
    loss_type_right: str | None
    loss_type_left: str | None
    configuration_right: str | None
    configuration_left: str | None
    asymmetry_flag: bool
    shift_flag: bool
    engine_version: str | None
    interpretation_text: str | None
    status: str
    version: int
    has_extended_high_frequencies: bool
    thresholds: list[ThresholdRead]
