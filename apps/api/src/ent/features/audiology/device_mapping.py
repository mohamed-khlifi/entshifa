"""Map hearing device and pediatric ORM rows to API schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ent.engines.audiology.candidacy import CandidacyResult
from ent.features.audiology.device_models import (
    HearingDevice,
    OmeEpisode,
    PediatricAudiologyRecord,
)
from ent.features.audiology.schemas.device_responses import (
    AidedThresholdRead,
    CandidacyEvaluationRead,
    ChecklistItemRead,
    HearingDeviceRead,
    OmeEpisodeRead,
    PediatricAudiologyRead,
)


def _decimal(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _aided_thresholds(raw: list[Any] | None) -> list[AidedThresholdRead] | None:
    if not raw:
        return None
    items: list[AidedThresholdRead] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        freq = row.get("frequency_hz") or row.get("frequencyHz")
        level = row.get("level_db") or row.get("levelDb")
        if freq is None or level is None:
            continue
        items.append(AidedThresholdRead(frequency_hz=int(freq), level_db=int(level)))
    return items or None


def _mapping_dates(raw: list[Any] | None) -> list[Any] | None:
    if not raw:
        return None
    return list(raw)


def hearing_device_read(row: HearingDevice) -> HearingDeviceRead:
    thresholds = _aided_thresholds(row.aided_thresholds)
    mapping = _mapping_dates(row.mapping_dates)
    return HearingDeviceRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        ear=row.ear,  # type: ignore[arg-type]
        device_type=row.device_type,  # type: ignore[arg-type]
        brand=row.brand,
        model=row.model,
        serial=row.serial,
        fitted_on=row.fitted_on,
        fitted_by=row.fitted_by,
        warranty_end=row.warranty_end,
        last_programmed_on=row.last_programmed_on,
        battery_type=row.battery_type,
        daily_use_hours=_decimal(row.daily_use_hours),
        satisfaction=row.satisfaction,
        status=row.status,  # type: ignore[arg-type]
        aided_thresholds=thresholds,
        surgeon=row.surgeon,
        surgery_date=row.surgery_date,
        electrode_array=row.electrode_array,
        implant_activation_date=row.implant_activation_date,
        mapping_dates=mapping,
        complications=row.complications,
        mri_conditions=row.mri_conditions,
        notes=row.notes,
        version=int(row.version),
    )


def pediatric_read(row: PediatricAudiologyRecord) -> PediatricAudiologyRead:
    milestones = row.speech_language_milestones
    milestone_map: dict[str, bool] | None = None
    if isinstance(milestones, dict):
        milestone_map = {str(k): bool(v) for k, v in milestones.items()}
    ha_by = (
        row.ha_candidacy_confirmed_by.public_id
        if row.ha_candidacy_confirmed_by is not None
        else None
    )
    ci_by = (
        row.ci_candidacy_confirmed_by.public_id
        if row.ci_candidacy_confirmed_by is not None
        else None
    )
    return PediatricAudiologyRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        screen_date=row.screen_date,
        screen_result_right=row.screen_result_right,  # type: ignore[arg-type]
        screen_result_left=row.screen_result_left,  # type: ignore[arg-type]
        rescreen_date=row.rescreen_date,
        rescreen_result_right=row.rescreen_result_right,  # type: ignore[arg-type]
        rescreen_result_left=row.rescreen_result_left,  # type: ignore[arg-type]
        diagnostic_abr_date=row.diagnostic_abr_date,
        diagnostic_abr_result_right=row.diagnostic_abr_result_right,  # type: ignore[arg-type]
        diagnostic_abr_result_left=row.diagnostic_abr_result_left,  # type: ignore[arg-type]
        permanent_hearing_loss=bool(row.permanent_hearing_loss),
        intervention_date=row.intervention_date,
        intervention_type=row.intervention_type,  # type: ignore[arg-type]
        screen_by_1m_status=row.screen_by_1m_status,
        diagnosis_by_3m_status=row.diagnosis_by_3m_status,
        intervention_by_6m_status=row.intervention_by_6m_status,
        ehdi_engine_version=row.ehdi_engine_version,
        speech_language_milestones=milestone_map,
        candidacy_snapshot=row.candidacy_snapshot,
        ha_candidacy_confirmed_at=row.ha_candidacy_confirmed_at,
        ha_candidacy_confirmed_by_public_id=ha_by,
        ci_candidacy_confirmed_at=row.ci_candidacy_confirmed_at,
        ci_candidacy_confirmed_by_public_id=ci_by,
        version=int(row.version),
    )


def ome_episode_read(row: OmeEpisode) -> OmeEpisodeRead:
    return OmeEpisodeRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=row.encounter.public_id if row.encounter else None,
        audiogram_public_id=row.audiogram.public_id if row.audiogram else None,
        tympanometry_public_id=row.tympanometry.public_id if row.tympanometry else None,
        laterality=row.laterality,  # type: ignore[arg-type]
        first_seen_on=row.first_seen_on,
        hearing_level_db=_decimal(row.hearing_level_db),
        watchful_waiting_start_on=row.watchful_waiting_start_on,
        watchful_waiting_due_on=row.watchful_waiting_due_on,
        status=row.status,  # type: ignore[arg-type]
        resolved_on=row.resolved_on,
        notes=row.notes,
        version=int(row.version),
    )


def candidacy_evaluation_read(
    result: CandidacyResult,
    *,
    engine_version: str,
    engine_reference: str,
) -> CandidacyEvaluationRead:
    return CandidacyEvaluationRead(
        hearing_aid_items=[
            ChecklistItemRead(code=item.code, met=item.met)
            for item in result.hearing_aid_items
        ],
        cochlear_implant_items=[
            ChecklistItemRead(code=item.code, met=item.met)
            for item in result.cochlear_implant_items
        ],
        hearing_aid_eligible=result.hearing_aid_eligible,
        cochlear_implant_eligible=result.cochlear_implant_eligible,
        engine_version=engine_version,
        engine_reference=engine_reference,
    )
