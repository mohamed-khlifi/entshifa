"""Map P4-03 test record ORM rows to API schemas."""

from __future__ import annotations

from decimal import Decimal

from ent.features.audiology.schemas.test_responses import (
    AbrResultRead,
    AcousticReflexRead,
    OaeBandRead,
    OaeResultRead,
    SpeechAudiometryRead,
    TympanometryRead,
)
from ent.features.audiology.test_records import (
    AbrResult,
    AcousticReflex,
    OaeResult,
    SpeechAudiometry,
    Tympanometry,
)


def _float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def speech_read(row: SpeechAudiometry) -> SpeechAudiometryRead:
    additional = row.additional_wrs_points
    if isinstance(additional, list):
        extra: list[dict[str, object]] | None = [
            dict(item) if isinstance(item, dict) else item for item in additional
        ]
    else:
        extra = None
    return SpeechAudiometryRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=row.encounter.public_id if row.encounter else None,
        audiogram_public_id=row.audiogram.public_id if row.audiogram else None,
        performed_at=row.performed_at,
        performed_by_public_id=row.performed_by.public_id,
        ear=row.ear,  # type: ignore[arg-type]
        srt_db=row.srt_db,
        sdt_db=row.sdt_db,
        wrs_percent=row.wrs_percent,
        wrs_level_db=row.wrs_level_db,
        additional_wrs_points=extra,
        word_list=row.word_list,
        list_locale=row.list_locale,
        mcl_db=row.mcl_db,
        ucl_db=row.ucl_db,
        rollover=row.rollover,
        sin_test=row.sin_test,
        sin_snr_db=_float(row.sin_snr_db),
        sin_score_percent=row.sin_score_percent,
        speech_pta_discrepancy_flag=bool(row.speech_pta_discrepancy_flag),
        version=int(row.version),
    )


def reflex_read(row: AcousticReflex) -> AcousticReflexRead:
    return AcousticReflexRead(
        stimulus_ear=row.stimulus_ear,  # type: ignore[arg-type]
        mode=row.mode,  # type: ignore[arg-type]
        frequency_hz=int(row.frequency_hz),
        threshold_db=row.threshold_db,
        status=row.status,  # type: ignore[arg-type]
    )


def tympanometry_read(row: Tympanometry) -> TympanometryRead:
    return TympanometryRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=row.encounter.public_id if row.encounter else None,
        performed_at=row.performed_at,
        performed_by_public_id=row.performed_by.public_id,
        ear=row.ear,  # type: ignore[arg-type]
        probe_tone_hz=int(row.probe_tone_hz),
        ecv_ml=_float(row.ecv_ml),
        peak_pressure_dapa=row.peak_pressure_dapa,
        compliance_ml=_float(row.compliance_ml),
        gradient_dapa=row.gradient_dapa,
        suggested_jerger_type=row.suggested_jerger_type,  # type: ignore[arg-type]
        jerger_type=row.jerger_type,  # type: ignore[arg-type]
        jerger_type_is_overridden=bool(row.jerger_type_is_overridden),
        overridden_by_public_id=(
            row.overridden_by.public_id if row.overridden_by is not None else None
        ),
        overridden_at=row.overridden_at,
        large_canal_volume_flag=bool(row.large_canal_volume_flag),
        etf_result=row.etf_result,  # type: ignore[arg-type]
        engine_version=row.engine_version,
        interpretation_text=row.interpretation_text,
        reflexes=[reflex_read(item) for item in row.reflexes],
        version=int(row.version),
    )


def oae_read(row: OaeResult) -> OaeResultRead:
    bands_raw = row.bands if isinstance(row.bands, list) else []
    bands = [
        OaeBandRead(
            frequency_hz=int(item.get("frequencyHz", item.get("frequency_hz", 0))),
            status=str(item.get("status", "")),
            snr_db=(
                float(item["snrDb"])
                if item.get("snrDb") is not None
                else (float(item["snr_db"]) if item.get("snr_db") is not None else None)
            ),
        )
        for item in bands_raw
        if isinstance(item, dict)
    ]
    return OaeResultRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=row.encounter.public_id if row.encounter else None,
        performed_at=row.performed_at,
        performed_by_public_id=row.performed_by.public_id,
        ear=row.ear,  # type: ignore[arg-type]
        oae_type=row.oae_type,  # type: ignore[arg-type]
        overall_result=row.overall_result,  # type: ignore[arg-type]
        screening_stage=row.screening_stage,  # type: ignore[arg-type]
        bands=bands,
        interpretation_text=row.interpretation_text,
        version=int(row.version),
    )


def abr_read(row: AbrResult) -> AbrResultRead:
    assr = row.assr_thresholds
    assr_list: list[dict[str, object]] | None = None
    if isinstance(assr, list):
        assr_list = [dict(item) if isinstance(item, dict) else item for item in assr]
    return AbrResultRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=row.encounter.public_id if row.encounter else None,
        performed_at=row.performed_at,
        performed_by_public_id=row.performed_by.public_id,
        ear=row.ear,  # type: ignore[arg-type]
        stimulus=row.stimulus,  # type: ignore[arg-type]
        stimulus_frequency_hz=row.stimulus_frequency_hz,
        threshold_db=row.threshold_db,
        intensity_db=row.intensity_db,
        wave_i_ms=_float(row.wave_i_ms),
        wave_iii_ms=_float(row.wave_iii_ms),
        wave_v_ms=_float(row.wave_v_ms),
        i_iii_ms=_float(row.i_iii_ms),
        iii_v_ms=_float(row.iii_v_ms),
        i_v_ms=_float(row.i_v_ms),
        interaural_v_diff_ms=_float(row.interaural_v_diff_ms),
        interaural_v_flag=bool(row.interaural_v_flag),
        assr_thresholds=assr_list,
        morphology=row.morphology,  # type: ignore[arg-type]
        engine_version=row.engine_version,
        interpretation_text=row.interpretation_text,
        version=int(row.version),
    )
