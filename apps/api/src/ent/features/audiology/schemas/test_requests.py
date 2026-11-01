"""P4-03 audiology test request schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ent.core.schemas.base import CamelModel
from ent.features.audiology.constants import (
    ACOUSTIC_REFLEX_FREQUENCIES_HZ,
    MAX_LEVEL_DB,
    MIN_LEVEL_DB,
    OAE_BAND_STATUSES,
    PROBE_TONE_HZ,
)
from ent.features.audiology.schemas.requests import AudiogramEar

JergerType = Literal["A", "As", "Ad", "B", "C"]
EtfResult = Literal["intact", "impaired", "patulous", "not_performed"]
ReflexMode = Literal["ipsi", "contra"]
ReflexStatus = Literal["present", "absent", "elevated", "not_tested"]
OaeType = Literal["teoae", "dpoae"]
OaeOverall = Literal["pass", "refer", "partial", "not_testable"]
OaeStage = Literal["first", "second", "diagnostic"]
OaeBandStatus = Literal["present", "absent", "partial"]
AbrStimulus = Literal["click", "tone_burst", "assr"]
AbrMorphology = Literal["normal", "poor", "absent", "reproducible"]


class AdditionalWrsPoint(CamelModel):
    level_db: int = Field(ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    wrs_percent: int = Field(ge=0, le=100)


class SpeechAudiometryCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    audiogram_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    ear: AudiogramEar
    srt_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    sdt_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    wrs_percent: int | None = Field(default=None, ge=0, le=100)
    wrs_level_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    additional_wrs_points: list[AdditionalWrsPoint] | None = None
    word_list: str | None = Field(default=None, max_length=60)
    list_locale: str | None = Field(default=None, max_length=10)
    mcl_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    ucl_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    rollover: bool | None = None
    sin_test: str | None = Field(default=None, max_length=60)
    sin_snr_db: Decimal | None = None
    sin_score_percent: int | None = Field(default=None, ge=0, le=100)


class SpeechAudiometryUpdate(CamelModel):
    version: int = Field(ge=1)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    audiogram_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    srt_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    sdt_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    wrs_percent: int | None = Field(default=None, ge=0, le=100)
    wrs_level_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    additional_wrs_points: list[AdditionalWrsPoint] | None = None
    word_list: str | None = Field(default=None, max_length=60)
    list_locale: str | None = Field(default=None, max_length=10)
    mcl_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    ucl_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    rollover: bool | None = None
    sin_test: str | None = Field(default=None, max_length=60)
    sin_snr_db: Decimal | None = None
    sin_score_percent: int | None = Field(default=None, ge=0, le=100)


class AcousticReflexInput(CamelModel):
    stimulus_ear: AudiogramEar
    mode: ReflexMode
    frequency_hz: int
    threshold_db: int | None = Field(default=None, ge=40, le=130)
    status: ReflexStatus

    @field_validator("frequency_hz")
    @classmethod
    def frequency_allowed(cls, value: int) -> int:
        if value not in ACOUSTIC_REFLEX_FREQUENCIES_HZ:
            msg = "frequency_hz"
            raise ValueError(msg)
        return value


class TympanometryCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    ear: AudiogramEar
    probe_tone_hz: int = 226
    ecv_ml: Decimal | None = None
    peak_pressure_dapa: int | None = Field(default=None, ge=-600, le=400)
    compliance_ml: Decimal | None = None
    gradient_dapa: int | None = Field(default=None, ge=0, le=600)
    etf_result: EtfResult | None = None
    jerger_type_override: JergerType | None = None
    reflexes: list[AcousticReflexInput] = Field(default_factory=list)

    @field_validator("probe_tone_hz")
    @classmethod
    def probe_allowed(cls, value: int) -> int:
        if value not in PROBE_TONE_HZ:
            msg = "probe_tone_hz"
            raise ValueError(msg)
        return value


class TympanometryUpdate(CamelModel):
    version: int = Field(ge=1)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    probe_tone_hz: int | None = None
    ecv_ml: Decimal | None = None
    peak_pressure_dapa: int | None = Field(default=None, ge=-600, le=400)
    compliance_ml: Decimal | None = None
    gradient_dapa: int | None = Field(default=None, ge=0, le=600)
    etf_result: EtfResult | None = None
    jerger_type_override: JergerType | None = None
    reflexes: list[AcousticReflexInput] | None = None


class TympanometryInterpret(CamelModel):
    version: int = Field(ge=1)
    interpretation_text: str | None = None
    jerger_type: JergerType | None = None


class OaeBandInput(CamelModel):
    frequency_hz: int = Field(ge=500, le=8000)
    status: OaeBandStatus
    snr_db: float | None = None

    @field_validator("status")
    @classmethod
    def status_allowed(cls, value: str) -> str:
        if value not in OAE_BAND_STATUSES:
            msg = "status"
            raise ValueError(msg)
        return value


class OaeResultCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    ear: AudiogramEar
    oae_type: OaeType
    overall_result: OaeOverall
    screening_stage: OaeStage | None = None
    bands: list[OaeBandInput] = Field(min_length=1)


class OaeResultUpdate(CamelModel):
    version: int = Field(ge=1)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    oae_type: OaeType | None = None
    overall_result: OaeOverall | None = None
    screening_stage: OaeStage | None = None
    bands: list[OaeBandInput] | None = None


class OaeInterpret(CamelModel):
    version: int = Field(ge=1)
    interpretation_text: str | None = None


class AssrThresholdInput(CamelModel):
    frequency_hz: int = Field(ge=500, le=4000)
    threshold_db: int = Field(ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)


class AbrResultCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    ear: AudiogramEar
    stimulus: AbrStimulus
    stimulus_frequency_hz: int | None = Field(default=None, ge=500, le=4000)
    threshold_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    intensity_db: int | None = Field(default=None, ge=0, le=130)
    wave_i_ms: Decimal | None = None
    wave_iii_ms: Decimal | None = None
    wave_v_ms: Decimal | None = None
    contralateral_wave_v_ms: Decimal | None = None
    assr_thresholds: list[AssrThresholdInput] | None = None
    morphology: AbrMorphology | None = None

    @model_validator(mode="after")
    def stimulus_frequency_rules(self) -> AbrResultCreate:
        if (
            self.stimulus in ("tone_burst", "assr")
            and self.stimulus_frequency_hz is None
        ):
            msg = "stimulus_frequency_hz"
            raise ValueError(msg)
        return self


class AbrResultUpdate(CamelModel):
    version: int = Field(ge=1)
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime | None = None
    performed_by_public_id: str | None = Field(
        default=None, min_length=26, max_length=26
    )
    stimulus: AbrStimulus | None = None
    stimulus_frequency_hz: int | None = Field(default=None, ge=500, le=4000)
    threshold_db: int | None = Field(default=None, ge=MIN_LEVEL_DB, le=MAX_LEVEL_DB)
    intensity_db: int | None = Field(default=None, ge=0, le=130)
    wave_i_ms: Decimal | None = None
    wave_iii_ms: Decimal | None = None
    wave_v_ms: Decimal | None = None
    contralateral_wave_v_ms: Decimal | None = None
    assr_thresholds: list[AssrThresholdInput] | None = None
    morphology: AbrMorphology | None = None


class AbrInterpret(CamelModel):
    version: int = Field(ge=1)
    interpretation_text: str | None = None
