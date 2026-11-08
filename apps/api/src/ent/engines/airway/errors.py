"""Airway calculator input errors."""

from __future__ import annotations


class AirwayInputError(Exception):
    def __init__(self, code: str, **context: str) -> None:
        self.code = code
        self.context = context
        super().__init__(code)
