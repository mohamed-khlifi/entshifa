"""EHDI 1-3-6 benchmark evaluation (feature spec §8.8 / JCIH 2019)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.ehdi_136"
REFERENCE = (
    "Joint Committee on Infant Hearing (JCIH) 2019 Position Statement — "
    "1-3-6 Early Hearing Detection and Intervention benchmarks"
)
FORMULA = (
    "screen_by_1m: screen_date <= birth_date + 30 days; "
    "diagnosis_by_3m: diagnostic_abr_date <= birth_date + 90 days when refer; "
    "intervention_by_6m: intervention_date <= birth_date + 180 days when loss"
)

SCREEN_BY_DAYS = 30
DIAGNOSIS_BY_DAYS = 90
INTERVENTION_BY_DAYS = 180


class BenchmarkStatus(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    MET = "met"
    LATE = "late"
    OVERDUE = "overdue"


@dataclass(frozen=True, slots=True)
class Ehdi136Input:
    birth_date: date
    as_of_date: date
    screen_date: date | None
    screen_refer: bool
    rescreen_date: date | None
    diagnostic_abr_date: date | None
    permanent_hearing_loss: bool
    intervention_date: date | None


@dataclass(frozen=True, slots=True)
class Ehdi136Result:
    screen_by_1m: BenchmarkStatus
    diagnosis_by_3m: BenchmarkStatus
    intervention_by_6m: BenchmarkStatus
    flags: tuple[Flag, ...]


def _days_from_birth(birth: date, event: date | None) -> int | None:
    if event is None:
        return None
    return (event - birth).days


def _status_for_deadline(
    *,
    event_days: int | None,
    deadline_days: int,
    as_of_days: int,
    required: bool,
) -> BenchmarkStatus:
    if not required:
        return BenchmarkStatus.NOT_APPLICABLE
    if event_days is not None:
        if event_days <= deadline_days:
            return BenchmarkStatus.MET
        return BenchmarkStatus.LATE
    if as_of_days > deadline_days:
        return BenchmarkStatus.OVERDUE
    return BenchmarkStatus.PENDING


def evaluate_ehdi_136(data: Ehdi136Input) -> Ehdi136Result:
    as_of_days = (data.as_of_date - data.birth_date).days
    screen_days = _days_from_birth(data.birth_date, data.screen_date)
    screen_required = True
    screen_status = _status_for_deadline(
        event_days=screen_days,
        deadline_days=SCREEN_BY_DAYS,
        as_of_days=as_of_days,
        required=screen_required,
    )

    needs_diagnosis = data.screen_refer or data.rescreen_date is not None
    diagnosis_days = _days_from_birth(data.birth_date, data.diagnostic_abr_date)
    diagnosis_status = _status_for_deadline(
        event_days=diagnosis_days,
        deadline_days=DIAGNOSIS_BY_DAYS,
        as_of_days=as_of_days,
        required=needs_diagnosis,
    )

    needs_intervention = data.permanent_hearing_loss
    intervention_days = _days_from_birth(data.birth_date, data.intervention_date)
    intervention_status = _status_for_deadline(
        event_days=intervention_days,
        deadline_days=INTERVENTION_BY_DAYS,
        as_of_days=as_of_days,
        required=needs_intervention,
    )

    flags: list[Flag] = []
    for name, status in (
        ("screen_by_1m", screen_status),
        ("diagnosis_by_3m", diagnosis_status),
        ("intervention_by_6m", intervention_status),
    ):
        if status in (BenchmarkStatus.LATE, BenchmarkStatus.OVERDUE):
            flags.append(
                Flag(
                    code=f"ehdi_{name}_{status.value}", detail={"status": status.value}
                )
            )

    return Ehdi136Result(
        screen_by_1m=screen_status,
        diagnosis_by_3m=diagnosis_status,
        intervention_by_6m=intervention_status,
        flags=tuple(flags),
    )


def ehdi_136_calculation(data: Ehdi136Input) -> CalculationResult:
    result = evaluate_ehdi_136(data)
    overdue = sum(
        1
        for status in (
            result.screen_by_1m,
            result.diagnosis_by_3m,
            result.intervention_by_6m,
        )
        if status == BenchmarkStatus.OVERDUE
    )
    return CalculationResult(
        code=CODE,
        value=str(overdue),
        unit="overdue_benchmark",
        inputs={
            "birthDate": data.birth_date.isoformat(),
            "asOfDate": data.as_of_date.isoformat(),
            "screenRefer": str(data.screen_refer),
            "permanentHearingLoss": str(data.permanent_hearing_loss),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=result.flags,
    )
