"""Typed failures for audiology calculators. Codes are stable; there is no sentence."""

from __future__ import annotations


class AudiometryInputError(Exception):
    """A metric cannot be computed from the supplied thresholds."""

    def __init__(self, code: str, **context: str) -> None:
        self.code = code
        self.context = context
        super().__init__(code)
