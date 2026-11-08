"""Ventilation tube candidacy checklist (feature spec §12.3)."""

from __future__ import annotations

from dataclasses import dataclass

from ent.engines.results import CalculationResult, Flag
from ent.engines.surgery.errors import SurgeryChecklistInputError

VERSION = "1.0.0"
CODE = "surgery.tube_criteria"
REFERENCE = (
    "Rosenfeld RM et al. AAO-HNS tympanostomy tubes guideline update 2022. "
    "Feature specification §12.3. # VERIFY: local guideline."
)
FORMULA = (
    "recurrent_aom: (>=3 AOM/6mo OR (>=4/12mo AND >=1/6mo)) AND effusion; "
    "persistent_ome: OME >=3 mo AND (bilateral+hearing difficulty OR at-risk/symptomatic)"
)


@dataclass(frozen=True, slots=True)
class TubeCriteriaInput:
    aom_episodes_6_months: int
    aom_episodes_12_months: int
    middle_ear_effusion_present: bool
    ome_duration_months: int
    bilateral_ome: bool
    hearing_difficulty_documented: bool
    at_risk_or_symptomatic_ome: bool


def _validate_count(value: int, field: str, maximum: int) -> None:
    if value < 0 or value > maximum:
        raise SurgeryChecklistInputError("surgery.tube_count_out_of_range", field=field)


def evaluate_tube_criteria(data: TubeCriteriaInput) -> tuple[bool, tuple[Flag, ...]]:
    _validate_count(data.aom_episodes_6_months, "aom_episodes_6_months", 24)
    _validate_count(data.aom_episodes_12_months, "aom_episodes_12_months", 36)
    if data.ome_duration_months < 0 or data.ome_duration_months > 60:
        raise SurgeryChecklistInputError(
            "surgery.tube_ome_duration_out_of_range",
            field="ome_duration_months",
        )
    recurrent_aom = data.middle_ear_effusion_present and (
        data.aom_episodes_6_months >= 3
        or (data.aom_episodes_12_months >= 4 and data.aom_episodes_6_months >= 1)
    )
    persistent_ome = data.ome_duration_months >= 3 and (
        (data.bilateral_ome and data.hearing_difficulty_documented)
        or data.at_risk_or_symptomatic_ome
    )
    met = recurrent_aom or persistent_ome
    flags: list[Flag] = [
        Flag(
            code="recurrent_aom_pathway_met",
            detail={"met": str(recurrent_aom).lower()},
        ),
        Flag(
            code="persistent_ome_pathway_met",
            detail={"met": str(persistent_ome).lower()},
        ),
    ]
    if met:
        flags.append(Flag(code="tube_criteria_met", detail={}))
    return met, tuple(flags)


def tube_criteria_checklist(data: TubeCriteriaInput) -> CalculationResult:
    met, flags = evaluate_tube_criteria(data)
    return CalculationResult(
        code=CODE,
        value="met" if met else "not_met",
        unit=None,
        inputs={
            "aom_episodes_6_months": str(data.aom_episodes_6_months),
            "aom_episodes_12_months": str(data.aom_episodes_12_months),
            "middle_ear_effusion_present": str(
                data.middle_ear_effusion_present
            ).lower(),
            "ome_duration_months": str(data.ome_duration_months),
            "bilateral_ome": str(data.bilateral_ome).lower(),
            "hearing_difficulty_documented": str(
                data.hearing_difficulty_documented
            ).lower(),
            "at_risk_or_symptomatic_ome": str(data.at_risk_or_symptomatic_ome).lower(),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=flags,
    )
