"""Typed failures for prescription engines. Codes are stable; there is no sentence."""

from __future__ import annotations


class EngineInputError(Exception):
    """The caller did not supply a computable input. ``code`` is namespaced."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
