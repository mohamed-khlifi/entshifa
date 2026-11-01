"""Recompute audiogram metrics when linked speech audiometry changes."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.principal import CurrentUser
from ent.engines.audiology.speech_agreement import speech_discrepancy
from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import SpeechEarInput
from ent.features.audiology.calc_settings import resolve_calc_settings
from ent.features.audiology.repository import AudiogramRepository
from ent.features.audiology.scoring import (
    apply_metrics_to_audiogram,
    compute_metrics,
    metric_rows_for_audiogram,
    threshold_points_from_rows,
)
from ent.features.audiology.test_records import SpeechAudiometry
from ent.features.audiology.test_repository import SpeechAudiometryRepository


async def sync_audiogram_for_speech(
    session: AsyncSession,
    user: CurrentUser,
    *,
    audiogram_id: int,
) -> None:
    audiograms = AudiogramRepository(session, clinic_id=user.clinic_id)
    row = await audiograms.get_detail_by_id(audiogram_id)
    if row is None or not row.thresholds:
        return
    speech_repo = SpeechAudiometryRepository(session, clinic_id=user.clinic_id)
    speech_rows = await speech_repo.list_for_audiogram(audiogram_id)
    speech_right, speech_left = _speech_inputs(speech_rows)
    pta_formula, asymmetry_rule, shift_rule = await resolve_calc_settings(session, user)
    baseline_points = None
    if row.baseline_audiogram_id is not None and row.baseline_audiogram is not None:
        if row.baseline_audiogram.thresholds:
            baseline_points = threshold_points_from_rows(
                list(row.baseline_audiogram.thresholds)
            )
    metrics = compute_metrics(
        thresholds=threshold_points_from_rows(list(row.thresholds)),
        pta_formula=pta_formula,
        asymmetry_rule=asymmetry_rule,
        shift_rule=shift_rule,
        baseline_thresholds=baseline_points,
        speech_right=speech_right,
        speech_left=speech_left,
    )
    apply_metrics_to_audiogram(row, metrics)
    await audiograms.replace_metrics(
        int(row.id),
        metric_rows_for_audiogram(
            audiogram=row,
            metrics=metrics,
            clinic_id=user.clinic_id,
            user_id=user.user_id,
        ),
        user_id=user.user_id,
    )
    indexed_dict = index_thresholds(threshold_points_from_rows(list(row.thresholds)))
    for speech in speech_rows:
        discrepancy = speech_discrepancy(
            indexed_dict,
            ear=speech.ear,
            srt_db=speech.srt_db,
            pta_formula=pta_formula,
        )
        speech.speech_pta_discrepancy_flag = discrepancy
        speech.updated_by_id = user.user_id


def _speech_inputs(
    rows: list[SpeechAudiometry],
) -> tuple[SpeechEarInput | None, SpeechEarInput | None]:
    right_srt: int | None = None
    right_wrs: int | None = None
    left_srt: int | None = None
    left_wrs: int | None = None
    for row in rows:
        if row.ear == "right":
            if row.srt_db is not None:
                right_srt = row.srt_db
            if row.wrs_percent is not None:
                right_wrs = row.wrs_percent
        else:
            if row.srt_db is not None:
                left_srt = row.srt_db
            if row.wrs_percent is not None:
                left_wrs = row.wrs_percent
    speech_right = (
        SpeechEarInput(srt_db=right_srt, wrs_percent=right_wrs)
        if right_srt is not None or right_wrs is not None
        else None
    )
    speech_left = (
        SpeechEarInput(srt_db=left_srt, wrs_percent=left_wrs)
        if left_srt is not None or left_wrs is not None
        else None
    )
    return speech_right, speech_left
