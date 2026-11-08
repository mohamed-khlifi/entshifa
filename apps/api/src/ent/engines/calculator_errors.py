"""Typed input errors for the calculator catalog (pure, no HTTP)."""

from __future__ import annotations


class CalculatorInputError(Exception):
    """Invalid calculator HTTP payload before the clinical engine runs."""

    def __init__(self, code: str, **context: str) -> None:
        self.code = code
        self.context = context
        super().__init__(code)
