"""Known-answer tests for EHDI 1-3-6 benchmarks (JCIH 2019)."""

from __future__ import annotations

from datetime import date

from ent.engines.audiology.ehdi_136 import (
    BenchmarkStatus,
    Ehdi136Input,
    ehdi_136_calculation,
    evaluate_ehdi_136,
)

# JCIH 2019: screen by 1 month (30 days), diagnose by 3 months (90 days),
# intervene by 6 months (180 days) when permanent loss is confirmed.


def test_screen_met_on_day_30() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 2, 1),
            screen_date=date(2026, 1, 31),
            screen_refer=False,
            rescreen_date=None,
            diagnostic_abr_date=None,
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert result.screen_by_1m == BenchmarkStatus.MET


def test_screen_overdue_after_day_30_without_screen() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 2, 5),
            screen_date=None,
            screen_refer=False,
            rescreen_date=None,
            diagnostic_abr_date=None,
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert result.screen_by_1m == BenchmarkStatus.OVERDUE


def test_screen_pending_before_day_30() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 1, 20),
            screen_date=None,
            screen_refer=False,
            rescreen_date=None,
            diagnostic_abr_date=None,
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert result.screen_by_1m == BenchmarkStatus.PENDING


def test_screen_late_after_day_30() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 2, 10),
            screen_date=date(2026, 2, 5),
            screen_refer=False,
            rescreen_date=None,
            diagnostic_abr_date=None,
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert result.screen_by_1m == BenchmarkStatus.LATE
    assert any(flag.code == "ehdi_screen_by_1m_late" for flag in result.flags)


def test_ehdi_136_calculation_counts_overdue() -> None:
    birth = date(2026, 1, 1)
    calc = ehdi_136_calculation(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 2, 5),
            screen_date=None,
            screen_refer=False,
            rescreen_date=None,
            diagnostic_abr_date=None,
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert calc.value == "1"
    assert calc.unit == "overdue_benchmark"


def test_diagnosis_met_on_day_90_when_referred() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 4, 1),
            screen_date=date(2026, 1, 15),
            screen_refer=True,
            rescreen_date=None,
            diagnostic_abr_date=date(2026, 3, 31),
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert result.diagnosis_by_3m == BenchmarkStatus.MET


def test_diagnosis_not_applicable_without_refer() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 4, 1),
            screen_date=date(2026, 1, 15),
            screen_refer=False,
            rescreen_date=None,
            diagnostic_abr_date=None,
            permanent_hearing_loss=False,
            intervention_date=None,
        )
    )
    assert result.diagnosis_by_3m == BenchmarkStatus.NOT_APPLICABLE


def test_intervention_late_after_day_180() -> None:
    birth = date(2026, 1, 1)
    result = evaluate_ehdi_136(
        Ehdi136Input(
            birth_date=birth,
            as_of_date=date(2026, 8, 1),
            screen_date=date(2026, 1, 10),
            screen_refer=True,
            rescreen_date=None,
            diagnostic_abr_date=date(2026, 3, 1),
            permanent_hearing_loss=True,
            intervention_date=date(2026, 7, 15),
        )
    )
    assert result.intervention_by_6m == BenchmarkStatus.LATE
