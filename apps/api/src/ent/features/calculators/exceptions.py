"""Calculator domain errors."""

from __future__ import annotations

from ent.core.errors.exceptions import NotFoundError, ValidationError


class CalculatorNotFoundError(NotFoundError):
    def __init__(self, *, code: str | None = None) -> None:
        super().__init__(resource="calculator", code=code)


class CalculatorNotInteractiveError(ValidationError):
    def __init__(self, *, code: str) -> None:
        super().__init__(calculator_code=code)


class CalculatorInvalidInputError(ValidationError):
    def __init__(self, *, reason: str, field: str | None = None) -> None:
        context: dict[str, str] = {"reason": reason}
        if field is not None:
            context["field"] = field
        super().__init__(**context)
