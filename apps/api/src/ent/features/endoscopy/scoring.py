"""Recompute endoscopy scores from stored observations. No database access."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ent.engines.endoscopy.adenoid import score as score_adenoid
from ent.engines.endoscopy.errors import ScoreInputError
from ent.engines.endoscopy.lund_kennedy import score as score_lund_kennedy
from ent.engines.endoscopy.modified_lund_kennedy import score as score_modified
from ent.engines.endoscopy.polyp_grade import score as score_polyp_grade
from ent.engines.results import CalculationResult
from ent.features.endoscopy.constants import (
    ADENOID_CODE,
    LK_ITEM_BY_CODE,
    MODIFIED_LK_ITEMS,
    POLYP_GRADE_CODE,
)
from ent.features.endoscopy.exceptions import (
    EndoscopyIncompleteScoreError,
    EndoscopyInvalidScoreError,
)


@dataclass(frozen=True, slots=True)
class ScoreRow:
    """One stored observation the engines are allowed to read."""

    concept_code: str
    laterality: str
    ordinal_value: int | None
    value_numeric: Decimal | None


@dataclass(frozen=True, slots=True)
class EndoscopyScores:
    """Engine outputs plus the integers persisted on ``endoscopy_exam``."""

    lund_kennedy: CalculationResult
    modified_lund_kennedy: CalculationResult
    polyp_grade: CalculationResult | None
    adenoid: CalculationResult | None
    lund_kennedy_right: int
    lund_kennedy_left: int
    modified_lk_right: int
    modified_lk_left: int
    polyp_grade_right: int | None
    polyp_grade_left: int | None
    adenoid_obstruction_pct: int | None


def compute(rows: list[ScoreRow], *, polyp_scale: str) -> EndoscopyScores:
    """Sum the score observations. Structure findings are ignored."""

    try:
        return _compute(rows, polyp_scale=polyp_scale)
    except ScoreInputError as exc:
        item = exc.context.get("item")
        side = exc.context.get("side")
        if exc.code == "endoscopy.incomplete_score":
            raise EndoscopyIncompleteScoreError(item=item, side=side) from exc
        raise EndoscopyInvalidScoreError(item=item, side=side) from exc


def _compute(rows: list[ScoreRow], *, polyp_scale: str) -> EndoscopyScores:
    right: dict[str, int] = {}
    left: dict[str, int] = {}
    polyp: dict[str, int] = {}
    adenoid: int | None = None
    for row in rows:
        if row.concept_code in LK_ITEM_BY_CODE:
            _put_lk_item(right, left, row)
        elif row.concept_code == POLYP_GRADE_CODE:
            polyp = _put_polyp(polyp, row)
        elif row.concept_code == ADENOID_CODE:
            adenoid = _put_adenoid(adenoid, row)
    lund = score_lund_kennedy(right=right, left=left)
    modified_right = {item: right[item] for item in MODIFIED_LK_ITEMS}
    modified_left = {item: left[item] for item in MODIFIED_LK_ITEMS}
    modified = score_modified(right=modified_right, left=modified_left)
    polyp_result, polyp_right, polyp_left = _polyp(polyp, polyp_scale)
    adenoid_result = None if adenoid is None else score_adenoid(percent=adenoid)
    return EndoscopyScores(
        lund_kennedy=lund,
        modified_lund_kennedy=modified,
        polyp_grade=polyp_result,
        adenoid=adenoid_result,
        lund_kennedy_right=_side_points(lund, "right"),
        lund_kennedy_left=_side_points(lund, "left"),
        modified_lk_right=_side_points(modified, "right"),
        modified_lk_left=_side_points(modified, "left"),
        polyp_grade_right=polyp_right,
        polyp_grade_left=polyp_left,
        adenoid_obstruction_pct=adenoid,
    )


def _put_lk_item(
    right: dict[str, int],
    left: dict[str, int],
    row: ScoreRow,
) -> None:
    item = LK_ITEM_BY_CODE[row.concept_code]
    if row.laterality == "right":
        bucket = right
    elif row.laterality == "left":
        bucket = left
    else:
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item=item,
            side=row.laterality,
        )
    if item in bucket:
        raise ScoreInputError("endoscopy.invalid_score", item=item, side=row.laterality)
    if row.ordinal_value is None:
        raise ScoreInputError(
            "endoscopy.incomplete_score",
            item=item,
            side=row.laterality,
        )
    bucket[item] = row.ordinal_value


def _put_polyp(bucket: dict[str, int], row: ScoreRow) -> dict[str, int]:
    if row.laterality not in {"right", "left"}:
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item="polyp_grade",
            side=row.laterality,
        )
    if row.laterality in bucket or row.ordinal_value is None:
        code = (
            "endoscopy.invalid_score"
            if row.laterality in bucket
            else "endoscopy.incomplete_score"
        )
        raise ScoreInputError(code, item="polyp_grade", side=row.laterality)
    copied = dict(bucket)
    copied[row.laterality] = row.ordinal_value
    return copied


def _put_adenoid(current: int | None, row: ScoreRow) -> int:
    if current is not None:
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item="adenoid_obstruction_pct",
            side="midline",
        )
    numeric = row.value_numeric
    if numeric is None or numeric != numeric.to_integral_value():
        raise ScoreInputError(
            "endoscopy.invalid_score",
            item="adenoid_obstruction_pct",
            side="midline",
        )
    return int(numeric)


def _polyp(
    grades: dict[str, int],
    scale: str,
) -> tuple[CalculationResult | None, int | None, int | None]:
    if not grades:
        return None, None, None
    if "right" not in grades or "left" not in grades:
        missing = "right" if "right" not in grades else "left"
        raise ScoreInputError(
            "endoscopy.incomplete_score",
            item="polyp_grade",
            side=missing,
        )
    result = score_polyp_grade(
        scale=scale,
        right=grades["right"],
        left=grades["left"],
    )
    return result, grades["right"], grades["left"]


def _side_points(result: CalculationResult, side: str) -> int:
    for flag in result.flags:
        if flag.code == "side_total" and flag.detail.get("side") == side:
            return int(flag.detail["points"])
    raise ScoreInputError("endoscopy.incomplete_score", item="side_total", side=side)
