"""Recompute laryngoscopy scores from stored observations. No database access."""

from __future__ import annotations

from dataclasses import dataclass

from ent.engines.laryngoscopy.errors import ScoreInputError
from ent.engines.laryngoscopy.grbas import score as score_grbas
from ent.engines.laryngoscopy.penetration_aspiration import score as score_pas
from ent.engines.laryngoscopy.reflux_finding_score import score as score_rfs
from ent.engines.results import CalculationResult
from ent.features.laryngoscopy.constants import (
    GRBAS_ITEM_BY_CODE,
    GRBAS_ITEMS,
    PAS_CODE,
    RFS_ITEM_BY_CODE,
)
from ent.features.laryngoscopy.exceptions import (
    LaryngoscopyIncompleteScoreError,
    LaryngoscopyInvalidScoreError,
)


@dataclass(frozen=True, slots=True)
class ScoreRow:
    """One stored observation the engines are allowed to read."""

    concept_code: str
    ordinal_value: int | None


@dataclass(frozen=True, slots=True)
class LaryngoscopyScores:
    """Engine outputs plus the integers persisted on ``laryngoscopy_exam``."""

    reflux_finding_score: CalculationResult | None
    grbas: CalculationResult | None
    penetration_aspiration: CalculationResult | None
    rfs_score: int | None
    grbas_g: int | None
    grbas_r: int | None
    grbas_b: int | None
    grbas_a: int | None
    grbas_s: int | None
    pas_score: int | None


def compute(rows: list[ScoreRow], *, fees_performed: bool) -> LaryngoscopyScores:
    """Sum the score observations. Structure findings are ignored."""

    try:
        return _compute(rows, fees_performed=fees_performed)
    except ScoreInputError as exc:
        item = exc.context.get("item")
        side = exc.context.get("side")
        if exc.code == "laryngoscopy.incomplete_score":
            raise LaryngoscopyIncompleteScoreError(item=item, side=side) from exc
        raise LaryngoscopyInvalidScoreError(item=item, side=side) from exc


def _compute(rows: list[ScoreRow], *, fees_performed: bool) -> LaryngoscopyScores:
    rfs: dict[str, int] = {}
    grbas: dict[str, int] = {}
    pas: int | None = None
    for row in rows:
        if row.ordinal_value is None:
            continue
        if row.concept_code in RFS_ITEM_BY_CODE:
            rfs[RFS_ITEM_BY_CODE[row.concept_code]] = row.ordinal_value
        elif row.concept_code in GRBAS_ITEM_BY_CODE:
            grbas[GRBAS_ITEM_BY_CODE[row.concept_code]] = row.ordinal_value
        elif row.concept_code == PAS_CODE:
            pas = row.ordinal_value
    rfs_result = score_rfs(items=rfs) if rfs else None
    grbas_result = score_grbas(items=grbas) if grbas else None
    if fees_performed and pas is None:
        raise ScoreInputError("laryngoscopy.incomplete_score", item="pas", side="na")
    if not fees_performed and pas is not None:
        raise ScoreInputError("laryngoscopy.invalid_score", item="pas", side="na")
    pas_result = score_pas(level=pas) if pas is not None else None
    components = {item: grbas[item] for item in GRBAS_ITEMS if item in grbas}
    return LaryngoscopyScores(
        reflux_finding_score=rfs_result,
        grbas=grbas_result,
        penetration_aspiration=pas_result,
        rfs_score=int(rfs_result.value) if rfs_result is not None else None,
        grbas_g=components.get("grade"),
        grbas_r=components.get("roughness"),
        grbas_b=components.get("breathiness"),
        grbas_a=components.get("asthenia"),
        grbas_s=components.get("strain"),
        pas_score=pas,
    )
