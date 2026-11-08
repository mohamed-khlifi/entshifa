"""Surgery checklist input errors."""

from __future__ import annotations


class SurgeryChecklistInputError(Exception):
    def __init__(self, code: str, **context: str) -> None:
        self.code = code
        self.context = context
        super().__init__(code)
