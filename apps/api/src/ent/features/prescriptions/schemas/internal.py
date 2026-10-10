"""Parse a stored formulary dosing document into engine inputs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from ent.engines.prescriptions.pediatric_dosing import AgeCap, DosingRule
from ent.engines.prescriptions.steroid_taper import TaperInput


class DosingDocumentError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParsedDosing:
    mg_per_kg_per_day: Decimal | None
    doses_per_day: int | None
    max_mg_per_day: Decimal | None
    default_duration_days: int | None
    age_caps: tuple[AgeCap, ...]
    taper: TaperInput | None
    indication_code: str | None


def _mapping(value: object, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DosingDocumentError(code)
    return value


def _decimal(value: object, code: str) -> Decimal:
    if (
        isinstance(value, bool)
        or isinstance(value, float)
        or not isinstance(value, (str, int, Decimal))
    ):
        raise DosingDocumentError(code)
    try:
        parsed = Decimal(value if isinstance(value, str) else str(value))
    except InvalidOperation as exc:
        raise DosingDocumentError(code) from exc
    if not parsed.is_finite():
        raise DosingDocumentError(code)
    return parsed


def _optional_decimal(payload: dict[str, Any], key: str) -> Decimal | None:
    if key not in payload or payload[key] is None:
        return None
    return _decimal(payload[key], "prescription.dosing_rule_invalid")


def _optional_int(payload: dict[str, Any], key: str) -> int | None:
    if key not in payload or payload[key] is None:
        return None
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise DosingDocumentError("prescription.dosing_rule_invalid")
    return int(value)


def _layer(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mg_per_kg_per_day": _optional_decimal(payload, "mg_per_kg_per_day"),
        "doses_per_day": _optional_int(payload, "doses_per_day"),
        "max_mg_per_day": _optional_decimal(payload, "max_mg_per_day"),
        "default_duration_days": _optional_int(payload, "default_duration_days"),
    }


def parse_dosing_document(
    document: dict[str, Any] | None,
    *,
    indication_code: str | None,
) -> ParsedDosing:
    """Merge an indication overlay onto the base rule. Floats are rejected."""

    if document is None:
        raise DosingDocumentError("prescription.dosing_rule_invalid")
    base = _layer(document)
    if indication_code:
        indications = document.get("indications") or {}
        if not isinstance(indications, dict) or indication_code not in indications:
            raise DosingDocumentError("prescription.dosing_rule_invalid")
        overlay = _layer(
            _mapping(indications[indication_code], "prescription.dosing_rule_invalid")
        )
        for key, value in overlay.items():
            if value is not None:
                base[key] = value

    caps: list[AgeCap] = []
    raw_caps = document.get("age_caps") or []
    if not isinstance(raw_caps, list):
        raise DosingDocumentError("prescription.dosing_rule_invalid")
    for raw in raw_caps:
        item = _mapping(raw, "prescription.dosing_rule_invalid")
        years = _optional_int(item, "max_completed_years")
        maximum = _optional_decimal(item, "max_mg_per_day")
        if years is None or maximum is None:
            raise DosingDocumentError("prescription.dosing_rule_invalid")
        caps.append(AgeCap(max_completed_years=years, max_mg_per_day=maximum))

    taper: TaperInput | None = None
    if document.get("taper") is not None:
        raw_taper = _mapping(document["taper"], "prescription.dosing_rule_invalid")
        start = _optional_decimal(raw_taper, "start_mg")
        step = _optional_decimal(raw_taper, "step_mg")
        days = _optional_int(raw_taper, "days_per_step")
        floor = _optional_decimal(raw_taper, "minimum_mg")
        if start is None or step is None or days is None or floor is None:
            raise DosingDocumentError("prescription.dosing_rule_invalid")
        taper = TaperInput(
            start_mg=start,
            step_mg=step,
            days_per_step=days,
            minimum_mg=floor,
        )

    mg_per_kg = base["mg_per_kg_per_day"]
    doses = base["doses_per_day"]
    maximum = base["max_mg_per_day"]
    duration = base["default_duration_days"]
    return ParsedDosing(
        mg_per_kg_per_day=mg_per_kg if isinstance(mg_per_kg, Decimal) else None,
        doses_per_day=doses if isinstance(doses, int) else None,
        max_mg_per_day=maximum if isinstance(maximum, Decimal) else None,
        default_duration_days=duration if isinstance(duration, int) else None,
        age_caps=tuple(caps),
        taper=taper,
        indication_code=indication_code,
    )


def as_dosing_rule(parsed: ParsedDosing) -> DosingRule:
    if parsed.mg_per_kg_per_day is None or parsed.doses_per_day is None:
        raise DosingDocumentError("prescription.dosing_rule_invalid")
    return DosingRule(
        mg_per_kg_per_day=parsed.mg_per_kg_per_day,
        doses_per_day=parsed.doses_per_day,
        max_mg_per_day=parsed.max_mg_per_day,
        indication_code=parsed.indication_code,
    )
