"""Dispatch scoring by instrument ``scoring_type`` (data-driven)."""

from __future__ import annotations

from decimal import Decimal

from ent.engines.scoring.errors import InvalidInstrumentDefinitionError
from ent.engines.scoring.sum_scorer import score_questionnaire
from ent.engines.scoring.types import InstrumentScoringSpec, QuestionnaireScoreOutput


def score_from_spec(
    spec: InstrumentScoringSpec,
    answers: dict[str, int],
    *,
    previous_total_score: Decimal | None = None,
) -> QuestionnaireScoreOutput:
    if spec.scoring_type not in ("sum", "weighted_sum"):
        raise InvalidInstrumentDefinitionError("custom_scorer_not_in_p5_01")
    return score_questionnaire(
        spec,
        answers,
        previous_total_score=previous_total_score,
    )
