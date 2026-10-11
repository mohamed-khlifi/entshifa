"""Typed failures for laryngoscopy scores. Codes are stable; there is no sentence."""

from __future__ import annotations


class ScoreInputError(Exception):
    """A score cannot be computed from the supplied observations."""

    def __init__(self, code: str, **context: str) -> None:
        self.code = code
        self.context = context
        super().__init__(code)
