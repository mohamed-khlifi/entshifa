"""Audiogram API request models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ent.core.schemas.base import CamelModel
from ent.features.audiology.constants import (
    ALL_FREQUENCIES_HZ,
    BONE_FREQUENCIES_HZ,
    MAX_LEVEL_DB,
    MIN_LEVEL_DB,
)

AudiogramEar = Literal["right", "left"]
AudiogramConduction = Literal["air", "bone"]
AudiogramTransducer = Literal["headphones", "inserts", "free_field", "bone_oscillator"]
AudiogramMethod = Literal["standard", "play", "vra", "boa", "soundfield"]
AudiogramReliability = Literal["good", "fair", "poor"]


class ThresholdInput(CamelModel):
    ear: AudiogramEar
    conduction: AudiogramConduction
    frequency_hz: int = Field(ge=125, le=16000)
    level_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    is_masked: bool = False
    is_no_response: bool = False

    @field_validator("frequency_hz")
    @classmethod
    def frequency_allowed(cls, value: int) -> int:
        if value not in ALL_FREQUENCIES_HZ:
            msg = "frequency_hz"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def bone_and_level_rules(self) -> ThresholdInput:
        if self.conduction == "bone" and self.frequency_hz not in BONE_FREQUENCIES_HZ:
            msg = "bone_frequency"
            raise ValueError(msg)
        if not self.is_no_response and self.level_db is None:
            msg = "level_db"
            raise ValueError(msg)
        return self


class AudiogramCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    equipment: str | None = Field(default=None, max_length=80)
    calibration_date: date | None = None
    transducer: AudiogramTransducer = "headphones"
    method: AudiogramMethod = "standard"
    reliability: AudiogramReliability = "good"
    is_baseline: bool = False
    baseline_audiogram_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    interpretation_text: str | None = None
    thresholds: list[ThresholdInput] = Field(default_factory=list)


class AudiogramUpdate(CamelModel):
    version: int = Field(ge=1)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    equipment: str | None = Field(default=None, max_length=80)
    calibration_date: date | None = None
    transducer: AudiogramTransducer | None = None
    method: AudiogramMethod | None = None
    reliability: AudiogramReliability | None = None
    is_baseline: bool | None = None
    baseline_audiogram_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    interpretation_text: str | None = None
    thresholds: list[ThresholdInput] | None = None


class AudiogramInterpret(CamelModel):
    version: int = Field(ge=1)
    interpretation_text: str | None = None
    is_baseline: bool | None = None


class AudiogramBaselineUpdate(CamelModel):
    version: int = Field(ge=1)
    is_baseline: bool = True


class AudiogramFinalize(CamelModel):
    version: int = Field(ge=1)
