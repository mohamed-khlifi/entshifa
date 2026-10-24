"""Suggest conductive, sensorineural or mixed loss (feature spec §8.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ent.engines.audiology.air_bone_gap import gaps_for_ear
from ent.engines.audiology.thresholds import index_thresholds, optional_levels
from ent.engines.audiology.types import ABG_FREQUENCIES_HZ, LossType, ThresholdPoint
from ent.engines.results import CalculationResult

VERSION = "1.0.0"
CODE = "audiology.loss_type"
REFERENCE = "Feature specification §8.5 (ABG >=15 dB at two or more frequencies)"
FORMULA = (
    "conductive when ABG>=15 at >=2 frequencies and mean bone <20 dB HL; "
    "mixed when ABG>=15 at >=2 and mean bone >=20; else sensorineural"
)
_ABG_THRESHOLD = 15
_BONE_NORMAL_MAX = 20


def classify_loss_type(
    indexed: Mapping[tuple[str, str, int], ThresholdPoint],
    *,
    ear: str,
) -> LossType:
    gaps = gaps_for_ear(indexed, ear=ear)
    significant = sum(1 for value in gaps.values() if value >= _ABG_THRESHOLD)
    if significant < 2:
        return "sensorineural"
    bone = optional_levels(
        indexed, ear=ear, conduction="bone", frequencies_hz=ABG_FREQUENCIES_HZ
    )
    if not bone:
        return "mixed"
    mean_bone = sum(bone.values()) / len(bone)
    if mean_bone < _BONE_NORMAL_MAX:
        return "conductive"
    return "mixed"


def score(
    *,
    thresholds: Sequence[ThresholdPoint],
    ear: str,
) -> CalculationResult:
    indexed = index_thresholds(thresholds)
    loss_type = classify_loss_type(indexed, ear=ear)
    return CalculationResult(
        code=CODE,
        value=loss_type,
        unit=None,
        inputs={"ear": ear},
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=(),
    )
