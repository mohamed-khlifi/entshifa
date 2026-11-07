"""Scoring engine domain errors (pure layer; raised before HTTP mapping)."""

from __future__ import annotations


class ScoringEngineError(Exception):
    """Base scoring failure."""


class InvalidInstrumentDefinitionError(ScoringEngineError):
    """Instrument spec or stored scoring_config is inconsistent."""


class IncompleteInstrumentResponseError(ScoringEngineError):
    """One or more required item answers are missing."""

    def __init__(self, *, missing_item_codes: tuple[str, ...]) -> None:
        self.missing_item_codes = missing_item_codes
        super().__init__("incomplete_response")


class InvalidInstrumentAnswerError(ScoringEngineError):
    """An answer value is outside the allowed option set."""

    def __init__(self, *, item_code: str, value: int) -> None:
        self.item_code = item_code
        self.value = value
        super().__init__(f"invalid_answer:{item_code}")


class InstrumentScoreOutOfRangeError(ScoringEngineError):
    """Computed total falls outside the instrument's documented range."""

    def __init__(self, *, total: str, min_score: str, max_score: str) -> None:
        self.total = total
        self.min_score = min_score
        self.max_score = max_score
        super().__init__("score_out_of_range")
