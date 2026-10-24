"""Compute all audiogram summary metrics for persistence (P4-02)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from ent.engines.audiology.air_bone_gap import average_gap, gaps_for_ear
from ent.engines.audiology.asymmetry import asymmetry_met
from ent.engines.audiology.configuration import describe_configuration
from ent.engines.audiology.errors import AudiometryInputError
from ent.engines.audiology.impairment import (
    binaural_impairment_percent,
    monaural_impairment_percent,
)
from ent.engines.audiology.loss_type import classify_loss_type
from ent.engines.audiology.pta import pure_tone_average
from ent.engines.audiology.speech_agreement import speech_discrepancy
from ent.engines.audiology.threshold_shift import significant_shift
from ent.engines.audiology.thresholds import index_thresholds
from ent.engines.audiology.types import (
    AsymmetryRule,
    AudiogramMetricsResult,
    Configuration,
    LossType,
    PtaFormula,
    ShiftRule,
    SpeechEarInput,
    ThresholdPoint,
    WhoGrade,
)
from ent.engines.audiology.who_grading import grade_from_pta, who_pta
from ent.engines.results import Flag

VERSION = "1.0.0"
REFERENCE = "Ent audiology metrics bundle; feature specification §8.5"


def compute_audiogram_metrics(
    *,
    thresholds: Sequence[ThresholdPoint],
    pta_formula: PtaFormula,
    asymmetry_rule: AsymmetryRule,
    shift_rule: ShiftRule,
    baseline_thresholds: Sequence[ThresholdPoint] | None = None,
    speech_right: SpeechEarInput | None = None,
    speech_left: SpeechEarInput | None = None,
) -> AudiogramMetricsResult:
    if not thresholds:
        raise AudiometryInputError("audiology.incomplete_threshold")
    indexed = index_thresholds(thresholds)
    pta_right = _optional_pta(indexed, ear="right", formula=pta_formula)
    pta_left = _optional_pta(indexed, ear="left", formula=pta_formula)
    abg_right = average_gap(gaps_for_ear(indexed, ear="right"))
    abg_left = average_gap(gaps_for_ear(indexed, ear="left"))
    grade_right = _optional_grade(indexed, ear="right")
    grade_left = _optional_grade(indexed, ear="left")
    loss_right = _optional_loss(indexed, ear="right")
    loss_left = _optional_loss(indexed, ear="left")
    config_right, _ = _optional_config(indexed, ear="right")
    config_left, _ = _optional_config(indexed, ear="left")
    impairment_right = monaural_impairment_percent(indexed, ear="right")
    impairment_left = monaural_impairment_percent(indexed, ear="left")
    impairment_binaural = binaural_impairment_percent(impairment_right, impairment_left)
    wrs_right = speech_right.wrs_percent if speech_right else None
    wrs_left = speech_left.wrs_percent if speech_left else None
    asymmetry_flag = asymmetry_met(
        indexed,
        rule=asymmetry_rule,
        speech_right=wrs_right,
        speech_left=wrs_left,
    )
    shift_flag = False
    if baseline_thresholds:
        shift_flag = significant_shift(
            list(thresholds),
            list(baseline_thresholds),
            rule=shift_rule,
        )
    srt_right = speech_right.srt_db if speech_right else None
    srt_left = speech_left.srt_db if speech_left else None
    speech_disc_right = speech_discrepancy(
        indexed, ear="right", srt_db=srt_right, pta_formula=pta_formula
    )
    speech_disc_left = speech_discrepancy(
        indexed, ear="left", srt_db=srt_left, pta_formula=pta_formula
    )
    return AudiogramMetricsResult(
        pta_formula=pta_formula,
        pta_right=pta_right,
        pta_left=pta_left,
        abg_right=abg_right,
        abg_left=abg_left,
        grade_right=grade_right,
        grade_left=grade_left,
        loss_type_right=loss_right,
        loss_type_left=loss_left,
        configuration_right=config_right,
        configuration_left=config_left,
        asymmetry_flag=asymmetry_flag,
        shift_flag=shift_flag,
        engine_version=VERSION,
        impairment_right_pct=impairment_right,
        impairment_left_pct=impairment_left,
        impairment_binaural_pct=impairment_binaural,
        speech_discrepancy_right=speech_disc_right,
        speech_discrepancy_left=speech_disc_left,
    )


def _optional_pta(
    indexed: dict[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
    formula: PtaFormula,
) -> Decimal | None:
    try:
        return pure_tone_average(indexed, ear=ear, formula=formula)
    except AudiometryInputError:
        return None


def _optional_grade(
    indexed: dict[tuple[str, str, int], ThresholdPoint], *, ear: str
) -> WhoGrade | None:
    try:
        return grade_from_pta(who_pta(indexed, ear=ear))
    except AudiometryInputError:
        return None


def _optional_loss(
    indexed: dict[tuple[str, str, int], ThresholdPoint], *, ear: str
) -> LossType | None:
    try:
        return classify_loss_type(indexed, ear=ear)
    except AudiometryInputError:
        return None


def _optional_config(
    indexed: dict[tuple[str, str, int], ThresholdPoint], *, ear: str
) -> tuple[Configuration | None, tuple[Flag, ...]]:
    try:
        return describe_configuration(indexed, ear=ear)
    except AudiometryInputError:
        return None, ()
