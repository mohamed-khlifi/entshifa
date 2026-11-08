"""General calculator input errors (pure layer)."""

from __future__ import annotations


class GeneralCalculatorInputError(Exception):
    """Inputs are out of range or inconsistent for a general calculator."""

    def __init__(self, code: str, **context: str) -> None:
        self.code = code
        self.context = context
        super().__init__(code)
