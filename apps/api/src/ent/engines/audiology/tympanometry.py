"""Jerger tympanogram classification (feature spec §8.3, appendix A)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.jerger_tympanogram"
REFERENCE = (
    "Jerger J. Clinical experience with impedance audiometry. "
    "Arch Otolaryngol. 1970;92(4):311-324; feature specification §8.3"
)
FORMULA = (
    "Jerger A/As/Ad/B/C from compliance_ml, peak_pressure_dapa, ecv_ml "
    "(226 Hz adult norms; VERIFY against clinic protocol)"
)

JergerType = Literal["A", "As", "Ad", "B", "C"]

# VERIFY: ASHA/Jerger 226 Hz adult cut-offs documented in feature spec §8.3.
_COMPLIANCE_NORMAL_MIN = Decimal("0.30")
_COMPLIANCE_NORMAL_MAX = Decimal("1.60")
_COMPLIANCE_FLAT_MAX = Decimal("0.20")
_COMPLIANCE_SHALLOW_MAX = Decimal("0.30")
_PEAK_TYPE_C_DAPA = -100
_LARGE_ECV_ML = Decimal("2.00")


@dataclass(frozen=True, slots=True)
class TympanogramInput:
    ecv_ml: Decimal | None
    peak_pressure_dapa: int | None
    compliance_ml: Decimal | None
    gradient_dapa: int | None = None


@dataclass(frozen=True, slots=True)
class TympanogramClassification:
    suggested_jerger_type: JergerType | None
    large_canal_volume_flag: bool
    flags: tuple[Flag, ...]


def classify_tympanogram(data: TympanogramInput) -> TympanogramClassification:
    """Suggest Jerger type from numeric tympanometry values."""

    compliance = data.compliance_ml
    peak = data.peak_pressure_dapa
    ecv = data.ecv_ml

    suggested: JergerType | None = None
    if compliance is not None:
        if compliance <= _COMPLIANCE_FLAT_MAX:
            suggested = "B"
        elif peak is not None and peak < _PEAK_TYPE_C_DAPA:
            suggested = "C"
        elif compliance > _COMPLIANCE_NORMAL_MAX:
            suggested = "Ad"
        elif compliance < _COMPLIANCE_NORMAL_MIN:
            suggested = "As"
        else:
            suggested = "A"
    elif peak is not None and peak < _PEAK_TYPE_C_DAPA:
        suggested = "C"

    flags: list[Flag] = []
    large_ecv = False
    if suggested == "B" and ecv is not None and ecv > _LARGE_ECV_ML:
        large_ecv = True
        flags.append(
            Flag(
                "consistent_with_perforation_or_patent_tube",
                {"ecv_ml": str(ecv), "jerger_type": "B"},
            )
        )

    return TympanogramClassification(
        suggested_jerger_type=suggested,
        large_canal_volume_flag=large_ecv,
        flags=tuple(flags),
    )


def score(data: TympanogramInput) -> CalculationResult:
    result = classify_tympanogram(data)
    value = result.suggested_jerger_type or ""
    return CalculationResult(
        code=CODE,
        value=value,
        unit=None,
        inputs={
            "compliance_ml": (
                str(data.compliance_ml) if data.compliance_ml is not None else ""
            ),
            "peak_pressure_dapa": (
                str(data.peak_pressure_dapa)
                if data.peak_pressure_dapa is not None
                else ""
            ),
            "ecv_ml": str(data.ecv_ml) if data.ecv_ml is not None else "",
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=result.flags,
    )
