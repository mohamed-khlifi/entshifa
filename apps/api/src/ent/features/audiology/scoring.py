"""Map audiogram rows to pure engines and apply denormalized metrics."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from ent.core.utils.ids import new_ulid
from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.metrics import compute_audiogram_metrics
from ent.engines.audiology.types import (
    AsymmetryRule,
    AudiogramMetricsResult,
    PtaFormula,
    ShiftRule,
    SpeechEarInput,
    ThresholdPoint,
)
from ent.features.audiology.exceptions import AudiogramIncompleteThresholdsError
from ent.features.audiology.models import Audiogram, AudiogramThreshold, AudiologyMetric
from ent.features.audiology.schemas.requests import ThresholdInput


def threshold_points_from_inputs(
    items: list[ThresholdInput],
) -> list[ThresholdPoint]:
    return [
        ThresholdPoint(
            ear=item.ear,
            conduction=item.conduction,
            frequency_hz=item.frequency_hz,
            level_db=item.level_db,
            is_masked=item.is_masked,
            is_no_response=item.is_no_response,
        )
        for item in items
    ]


def threshold_points_from_rows(
    rows: list[AudiogramThreshold],
) -> list[ThresholdPoint]:
    return [
        ThresholdPoint(
            ear=row.ear,  # type: ignore[arg-type]
            conduction=row.conduction,  # type: ignore[arg-type]
            frequency_hz=int(row.frequency_hz),
            level_db=row.level_db,
            is_masked=bool(row.is_masked),
            is_no_response=bool(row.is_no_response),
        )
        for row in rows
    ]


def compute_metrics(
    *,
    thresholds: list[ThresholdPoint],
    pta_formula: PtaFormula,
    asymmetry_rule: AsymmetryRule,
    shift_rule: ShiftRule,
    baseline_thresholds: list[ThresholdPoint] | None = None,
    speech_right: SpeechEarInput | None = None,
    speech_left: SpeechEarInput | None = None,
    require_complete: bool = False,
) -> AudiogramMetricsResult:
    try:
        return compute_audiogram_metrics(
            thresholds=thresholds,
            pta_formula=pta_formula,
            asymmetry_rule=asymmetry_rule,
            shift_rule=shift_rule,
            baseline_thresholds=baseline_thresholds,
            speech_right=speech_right,
            speech_left=speech_left,
        )
    except AudiometryInputError as exc:
        if require_complete:
            raise AudiogramIncompleteThresholdsError() from exc
        raise


def apply_metrics_to_audiogram(row: Audiogram, metrics: AudiogramMetricsResult) -> None:
    row.pta_formula = metrics.pta_formula
    row.pta_right = metrics.pta_right
    row.pta_left = metrics.pta_left
    row.abg_right = metrics.abg_right
    row.abg_left = metrics.abg_left
    row.grade_right = metrics.grade_right
    row.grade_left = metrics.grade_left
    row.loss_type_right = metrics.loss_type_right
    row.loss_type_left = metrics.loss_type_left
    row.configuration_right = metrics.configuration_right
    row.configuration_left = metrics.configuration_left
    row.asymmetry_flag = metrics.asymmetry_flag
    row.shift_flag = metrics.shift_flag
    row.engine_version = metrics.engine_version


def metric_rows_for_audiogram(
    *,
    audiogram: Audiogram,
    metrics: AudiogramMetricsResult,
    clinic_id: int,
    user_id: int,
) -> list[AudiologyMetric]:
    now = datetime.now(UTC).replace(tzinfo=None)
    specs: list[tuple[str, str | None, Decimal | None, str | None]] = [
        ("audiology.pta", "right", metrics.pta_right, "dB HL"),
        ("audiology.pta", "left", metrics.pta_left, "dB HL"),
        ("audiology.abg_avg", "right", metrics.abg_right, "dB"),
        ("audiology.abg_avg", "left", metrics.abg_left, "dB"),
        (
            "audiology.impairment_monaural",
            "right",
            metrics.impairment_right_pct,
            "%",
        ),
        (
            "audiology.impairment_monaural",
            "left",
            metrics.impairment_left_pct,
            "%",
        ),
        (
            "audiology.impairment_binaural",
            None,
            metrics.impairment_binaural_pct,
            "%",
        ),
    ]
    rows: list[AudiologyMetric] = []
    for code, ear, value, unit in specs:
        if value is None:
            continue
        rows.append(
            AudiologyMetric(
                public_id=new_ulid(),
                clinic_id=clinic_id,
                audiogram_id=int(audiogram.id),
                metric_code=code,
                ear=ear,
                value=value,
                unit=unit,
                formula=f"pta_formula={metrics.pta_formula}",
                engine_version=metrics.engine_version,
                computed_at=now,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
        )
    return rows
