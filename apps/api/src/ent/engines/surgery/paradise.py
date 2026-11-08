"""Paradise criteria for tonsillectomy in recurrent tonsillitis (feature spec §12.3)."""

from __future__ import annotations

from dataclasses import dataclass

from ent.engines.results import CalculationResult, Flag
from ent.engines.surgery.errors import SurgeryChecklistInputError

VERSION = "1.0.0"
CODE = "surgery.paradise_criteria"
REFERENCE = (
    "Paradise JL et al. N Engl J Med 1984;310(11):674-683. "
    "Mitchell RB et al. AAO-HNS tonsillectomy guideline update 2019. "
    "Feature specification §12.3. # VERIFY: local guideline."
)
FORMULA = (
    "(>=7/yr OR >=5/yr for 2 yr OR >=3/yr for 3 yr) AND clinical feature "
    "AND episodes_documented"
)


@dataclass(frozen=True, slots=True)
class ParadiseInput:
    episodes_last_year: int
    episodes_year_2: int
    episodes_year_3: int
    fever_38_3c: bool
    cervical_adenopathy: bool
    tonsillar_exudate: bool
    positive_strep_a: bool
    episodes_documented: bool


def _validate_count(value: int, field: str) -> None:
    if value < 0 or value > 30:
        raise SurgeryChecklistInputError(
            "surgery.paradise_count_out_of_range", field=field
        )


def _frequency_met(data: ParadiseInput) -> tuple[bool, str | None]:
    if data.episodes_last_year >= 7:
        return True, "one_year_7"
    if data.episodes_year_2 >= 5:
        return True, "two_year_5_each"
    if data.episodes_year_3 >= 3:
        return True, "three_year_3_each"
    return False, None


def _clinical_feature(data: ParadiseInput) -> bool:
    return (
        data.fever_38_3c
        or data.cervical_adenopathy
        or data.tonsillar_exudate
        or data.positive_strep_a
    )


def evaluate_paradise(data: ParadiseInput) -> tuple[bool, tuple[Flag, ...]]:
    _validate_count(data.episodes_last_year, "episodes_last_year")
    _validate_count(data.episodes_year_2, "episodes_year_2")
    _validate_count(data.episodes_year_3, "episodes_year_3")
    frequency, tier = _frequency_met(data)
    clinical = _clinical_feature(data)
    documented = data.episodes_documented
    met = frequency and clinical and documented
    flags: list[Flag] = [
        Flag(
            code="frequency_tier_met",
            detail={"met": str(frequency).lower(), "tier": tier or ""},
        ),
        Flag(code="clinical_feature_present", detail={"met": str(clinical).lower()}),
        Flag(code="episodes_documented", detail={"met": str(documented).lower()}),
    ]
    if met:
        flags.append(Flag(code="paradise_criteria_met", detail={}))
    return met, tuple(flags)


def paradise_checklist(data: ParadiseInput) -> CalculationResult:
    met, flags = evaluate_paradise(data)
    return CalculationResult(
        code=CODE,
        value="met" if met else "not_met",
        unit=None,
        inputs={
            "episodes_last_year": str(data.episodes_last_year),
            "episodes_year_2": str(data.episodes_year_2),
            "episodes_year_3": str(data.episodes_year_3),
            "fever_38_3c": str(data.fever_38_3c).lower(),
            "cervical_adenopathy": str(data.cervical_adenopathy).lower(),
            "tonsillar_exudate": str(data.tonsillar_exudate).lower(),
            "positive_strep_a": str(data.positive_strep_a).lower(),
            "episodes_documented": str(data.episodes_documented).lower(),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=flags,
    )
