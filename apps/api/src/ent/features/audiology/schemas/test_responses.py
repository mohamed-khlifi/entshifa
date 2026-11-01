"""P4-03 audiology test response schemas."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import CamelModel
from ent.features.audiology.schemas.requests import AudiogramEar
from ent.features.audiology.schemas.test_requests import (
    AbrMorphology,
    AbrStimulus,
    EtfResult,
    JergerType,
    OaeOverall,
    OaeStage,
    OaeType,
    ReflexMode,
    ReflexStatus,
)


class AcousticReflexRead(CamelModel):
    stimulus_ear: AudiogramEar
    mode: ReflexMode
    frequency_hz: int
    threshold_db: int | None
    status: ReflexStatus


class SpeechAudiometryRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    audiogram_public_id: str | None
    performed_at: datetime
    performed_by_public_id: str
    ear: AudiogramEar
    srt_db: int | None
    sdt_db: int | None
    wrs_percent: int | None
    wrs_level_db: int | None
    additional_wrs_points: list[dict[str, object]] | None
    word_list: str | None
    list_locale: str | None
    mcl_db: int | None
    ucl_db: int | None
    rollover: bool | None
    sin_test: str | None
    sin_snr_db: float | None
    sin_score_percent: int | None
    speech_pta_discrepancy_flag: bool
    version: int


class TympanometryRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    performed_at: datetime
    performed_by_public_id: str
    ear: AudiogramEar
    probe_tone_hz: int
    ecv_ml: float | None
    peak_pressure_dapa: int | None
    compliance_ml: float | None
    gradient_dapa: int | None
    suggested_jerger_type: JergerType | None
    jerger_type: JergerType | None
    jerger_type_is_overridden: bool
    overridden_by_public_id: str | None
    overridden_at: datetime | None
    large_canal_volume_flag: bool
    etf_result: EtfResult | None
    engine_version: str | None
    interpretation_text: str | None
    reflexes: list[AcousticReflexRead]
    version: int


class OaeBandRead(CamelModel):
    frequency_hz: int
    status: str
    snr_db: float | None


class OaeResultRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    performed_at: datetime
    performed_by_public_id: str
    ear: AudiogramEar
    oae_type: OaeType
    overall_result: OaeOverall
    screening_stage: OaeStage | None
    bands: list[OaeBandRead]
    interpretation_text: str | None
    version: int


class AbrResultRead(CamelModel):
    public_id: str
    patient_public_id: str
    encounter_public_id: str | None
    performed_at: datetime
    performed_by_public_id: str
    ear: AudiogramEar
    stimulus: AbrStimulus
    stimulus_frequency_hz: int | None
    threshold_db: int | None
    intensity_db: int | None
    wave_i_ms: float | None
    wave_iii_ms: float | None
    wave_v_ms: float | None
    i_iii_ms: float | None
    iii_v_ms: float | None
    i_v_ms: float | None
    interaural_v_diff_ms: float | None
    interaural_v_flag: bool
    assr_thresholds: list[dict[str, object]] | None
    morphology: AbrMorphology | None
    engine_version: str | None
    interpretation_text: str | None
    version: int
