"""Parse flat calculator request maps into typed engine inputs (pure)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from ent.engines.audiology.types import ThresholdPoint
from ent.engines.calculator_errors import CalculatorInputError

Ear = Literal["right", "left"]
Conduction = Literal["air", "bone"]


def require_str(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if value is None or value == "":
        raise CalculatorInputError("calculator.missing_field", field=key)
    return str(value)


def optional_str(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None or value == "":
        return None
    return str(value)


def require_int(
    raw: Mapping[str, Any], key: str, *, minimum: int | None, maximum: int | None
) -> int:
    value = raw.get(key)
    if value is None or value == "":
        raise CalculatorInputError("calculator.missing_field", field=key)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CalculatorInputError("calculator.invalid_integer", field=key) from exc
    if isinstance(value, bool):
        raise CalculatorInputError("calculator.invalid_integer", field=key)
    if minimum is not None and parsed < minimum:
        raise CalculatorInputError("calculator.out_of_range", field=key)
    if maximum is not None and parsed > maximum:
        raise CalculatorInputError("calculator.out_of_range", field=key)
    return parsed


def optional_int(
    raw: Mapping[str, Any],
    key: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    value = raw.get(key)
    if value is None or value == "":
        return None
    return require_int(raw, key, minimum=minimum, maximum=maximum)


def require_bool(raw: Mapping[str, Any], key: str) -> bool:
    value = raw.get(key)
    if value is None or value == "":
        raise CalculatorInputError("calculator.missing_field", field=key)
    if isinstance(value, bool):
        return value
    text = str(value).lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    raise CalculatorInputError("calculator.invalid_boolean", field=key)


def optional_bool(raw: Mapping[str, Any], key: str) -> bool | None:
    value = raw.get(key)
    if value is None or value == "":
        return None
    return require_bool(raw, key)


def require_decimal(raw: Mapping[str, Any], key: str) -> Decimal:
    value = raw.get(key)
    if value is None or value == "":
        raise CalculatorInputError("calculator.missing_field", field=key)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CalculatorInputError("calculator.invalid_decimal", field=key) from exc


def optional_decimal(raw: Mapping[str, Any], key: str) -> Decimal | None:
    value = raw.get(key)
    if value is None or value == "":
        return None
    return require_decimal(raw, key)


def require_date(raw: Mapping[str, Any], key: str) -> date:
    text = require_str(raw, key)
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise CalculatorInputError("calculator.invalid_date", field=key) from exc


def optional_date(raw: Mapping[str, Any], key: str) -> date | None:
    text = optional_str(raw, key)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise CalculatorInputError("calculator.invalid_date", field=key) from exc


def threshold_level(
    raw: Mapping[str, Any],
    *,
    conduction: Conduction,
    ear: Ear,
    frequency_hz: int,
    prefix: str = "",
    required: bool = False,
) -> int | None:
    key = f"{prefix}{conduction}_{ear}_{frequency_hz}"
    value = raw.get(key)
    if value is None or value == "":
        if required:
            raise CalculatorInputError("calculator.missing_field", field=key)
        return None
    return require_int(raw, key, minimum=-10, maximum=120)


def collect_thresholds(
    raw: Mapping[str, Any],
    *,
    frequencies_hz: tuple[int, ...],
    ears: tuple[Ear, ...] = ("right", "left"),
    conductions: tuple[Conduction, ...] = ("air", "bone"),
    prefix: str = "",
) -> list[ThresholdPoint]:
    points: list[ThresholdPoint] = []
    for ear in ears:
        for conduction in conductions:
            for frequency_hz in frequencies_hz:
                level = threshold_level(
                    raw,
                    conduction=conduction,
                    ear=ear,
                    frequency_hz=frequency_hz,
                    prefix=prefix,
                )
                if level is None:
                    continue
                points.append(
                    ThresholdPoint(
                        ear=ear,
                        conduction=conduction,
                        frequency_hz=frequency_hz,
                        level_db=level,
                        is_masked=False,
                        is_no_response=False,
                    )
                )
    return points


def domain_from_code(code: str) -> str:
    return code.split(".", 1)[0]
