"""Calculator catalog. The generic calculator HTTP API arrives in phase 5."""

from __future__ import annotations

from dataclasses import dataclass

from ent.engines.prescriptions.pediatric_dosing import (
    CODE as PEDIATRIC_CODE,
)
from ent.engines.prescriptions.pediatric_dosing import (
    FORMULA as PEDIATRIC_FORMULA,
)
from ent.engines.prescriptions.pediatric_dosing import (
    REFERENCE as PEDIATRIC_REFERENCE,
)
from ent.engines.prescriptions.pediatric_dosing import (
    VERSION as PEDIATRIC_VERSION,
)
from ent.engines.prescriptions.steroid_taper import CODE as TAPER_CODE
from ent.engines.prescriptions.steroid_taper import FORMULA as TAPER_FORMULA
from ent.engines.prescriptions.steroid_taper import REFERENCE as TAPER_REFERENCE
from ent.engines.prescriptions.steroid_taper import VERSION as TAPER_VERSION


@dataclass(frozen=True, slots=True)
class CalculatorSpec:
    code: str
    version: str
    reference: str
    unit: str | None
    formula: str


def registered_calculators() -> tuple[CalculatorSpec, ...]:
    """Metadata for engines that must stay discoverable without new UI code."""

    return (
        CalculatorSpec(
            code=PEDIATRIC_CODE,
            version=PEDIATRIC_VERSION,
            reference=PEDIATRIC_REFERENCE,
            unit="mg",
            formula=PEDIATRIC_FORMULA,
        ),
        CalculatorSpec(
            code=TAPER_CODE,
            version=TAPER_VERSION,
            reference=TAPER_REFERENCE,
            unit="day",
            formula=TAPER_FORMULA,
        ),
    )
