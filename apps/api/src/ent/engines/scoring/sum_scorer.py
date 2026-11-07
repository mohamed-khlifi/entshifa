"""Generic sum and weighted-sum questionnaire scorer.

Supports reverse-scored items, per-item weights, scale multipliers (e.g. NOSE),
subscales and severity bands from instrument ``scoring_config`` data.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from ent.engines.results import CalculationResult, Flag
from ent.engines.scoring.errors import (
    IncompleteInstrumentResponseError,
    InstrumentScoreOutOfRangeError,
    InvalidInstrumentAnswerError,
    InvalidInstrumentDefinitionError,
)
from ent.engines.scoring.types import (
    InstrumentItemSpec,
    InstrumentScoringSpec,
    QuestionnaireScoreOutput,
    SeverityBandSpec,
)

VERSION = "1.0.0"
CODE = "scoring.questionnaire_sum"
REFERENCE = "ENT questionnaire engine: sum and weighted-sum (feature spec Appendix A)"
FORMULA = (
    "total = scale_multiplier * sum(effective_value * item_weight); "
    "effective_value = reverse(option_min, option_max, raw) when reverse-scored"
)


def _decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def validate_spec(spec: InstrumentScoringSpec) -> None:
    if not spec.items:
        raise InvalidInstrumentDefinitionError("items_required")
    if spec.scale_multiplier <= 0:
        raise InvalidInstrumentDefinitionError("multiplier_must_be_positive")
    if spec.min_score > spec.max_score:
        raise InvalidInstrumentDefinitionError("min_greater_than_max")
    codes: set[str] = set()
    for item in spec.items:
        if item.code in codes:
            raise InvalidInstrumentDefinitionError(f"duplicate_item:{item.code}")
        codes.add(item.code)
        if not item.allowed_values:
            raise InvalidInstrumentDefinitionError(f"empty_options:{item.code}")
        if item.weight <= 0:
            raise InvalidInstrumentDefinitionError(f"non_positive_weight:{item.code}")
    for band in spec.severity_bands:
        if band.min_score > band.max_score:
            raise InvalidInstrumentDefinitionError(f"invalid_band:{band.code}")
    known = frozenset(codes)
    for sub in spec.subscales:
        for item_code in sub.item_codes:
            if item_code not in known:
                raise InvalidInstrumentDefinitionError(
                    f"unknown_subscale_item:{sub.code}:{item_code}"
                )


def _effective_value(item: InstrumentItemSpec, raw: int) -> Decimal:
    if raw not in item.allowed_values:
        raise InvalidInstrumentAnswerError(item_code=item.code, value=raw)
    if not item.is_reverse_scored:
        return _decimal(raw)
    lo = min(item.allowed_values)
    hi = max(item.allowed_values)
    return _decimal(lo + hi - raw)


def _item_weight(spec: InstrumentScoringSpec, item: InstrumentItemSpec) -> Decimal:
    if spec.scoring_type == "sum":
        return Decimal("1")
    return item.weight


def _resolve_severity(
    total: Decimal, bands: tuple[SeverityBandSpec, ...]
) -> str | None:
    for band in bands:
        if band.min_score <= total <= band.max_score:
            return band.code
    return None


def _subscale_totals(
    spec: InstrumentScoringSpec,
    item_scores: Mapping[str, Decimal],
) -> dict[str, Decimal]:
    if spec.subscales:
        totals: dict[str, Decimal] = {}
        for sub in spec.subscales:
            total = Decimal("0")
            for code in sub.item_codes:
                total += item_scores[code]
            totals[sub.code] = total
        return totals
    by_tag: dict[str, Decimal] = {}
    for item in spec.items:
        if not item.subscale:
            continue
        by_tag[item.subscale] = (
            by_tag.get(item.subscale, Decimal("0")) + item_scores[item.code]
        )
    return by_tag


def score_questionnaire(
    spec: InstrumentScoringSpec,
    answers: Mapping[str, int],
    *,
    previous_total_score: Decimal | None = None,
) -> QuestionnaireScoreOutput:
    """Score a complete response. Missing items raise; never impute zero."""

    validate_spec(spec)
    required = {item.code for item in spec.items}
    provided = set(answers)
    missing = tuple(sorted(required - provided))
    if missing:
        raise IncompleteInstrumentResponseError(missing_item_codes=missing)
    unknown = provided - required
    if unknown:
        raise InvalidInstrumentAnswerError(
            item_code=sorted(unknown)[0],
            value=answers[sorted(unknown)[0]],
        )

    item_scores: dict[str, Decimal] = {}
    weighted_sum = Decimal("0")
    for item in spec.items:
        raw = answers[item.code]
        effective = _effective_value(item, raw)
        weight = _item_weight(spec, item)
        item_scores[item.code] = effective * weight
        weighted_sum += item_scores[item.code]

    total = (weighted_sum * spec.scale_multiplier).quantize(Decimal("0.01"))
    if total < spec.min_score or total > spec.max_score:
        raise InstrumentScoreOutOfRangeError(
            total=str(total),
            min_score=str(spec.min_score),
            max_score=str(spec.max_score),
        )

    subscale_scores = _subscale_totals(spec, item_scores)
    severity_band = _resolve_severity(total, spec.severity_bands)

    change: Decimal | None = None
    mcid_reached: bool | None = None
    if previous_total_score is not None:
        change = (total - previous_total_score).quantize(Decimal("0.01"))
        if spec.mcid is not None:
            mcid_reached = abs(change) >= spec.mcid

    flags: list[Flag] = []
    if severity_band is not None:
        flags.append(Flag(code="severity_band", detail={"code": severity_band}))
    if change is not None:
        flags.append(Flag(code="change_from_previous", detail={"points": str(change)}))
    if mcid_reached is not None:
        flags.append(
            Flag(code="mcid_reached", detail={"reached": str(mcid_reached).lower()})
        )
    for code, points in subscale_scores.items():
        flags.append(
            Flag(code="subscale", detail={"code": code, "points": str(points)})
        )

    inputs = {code: str(value) for code, value in answers.items()}
    calculation = CalculationResult(
        code=CODE,
        value=str(total),
        unit="points",
        inputs=inputs,
        formula=FORMULA,
        version=VERSION,
        reference=spec.reference or REFERENCE,
        flags=tuple(flags),
    )
    return QuestionnaireScoreOutput(
        calculation=calculation,
        total_score=total,
        item_scores=item_scores,
        subscale_scores=subscale_scores,
        severity_band=severity_band,
        change_from_previous=change,
        mcid_reached=mcid_reached,
    )
