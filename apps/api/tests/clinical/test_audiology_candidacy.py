"""Known-answer tests for hearing device candidacy (feature spec §8.7)."""

from __future__ import annotations

from decimal import Decimal

from ent.engines.audiology.candidacy import CandidacyInput, evaluate_device_candidacy


def test_hearing_aid_candidacy_when_pta_elevated_and_documented() -> None:
    result = evaluate_device_candidacy(
        CandidacyInput(
            pta_right=Decimal("35"),
            pta_left=Decimal("25"),
            wrs_right_percent=88,
            wrs_left_percent=92,
            loss_type_right="sensorineural",
            loss_type_left="sensorineural",
            hearing_aid_trial_completed=False,
            imaging_clearance=False,
            communication_impact_assessed=True,
        )
    )
    assert result.hearing_aid_eligible is True
    assert result.cochlear_implant_eligible is False


def test_cochlear_implant_boundary_pta_70_and_wrs_50() -> None:
    result = evaluate_device_candidacy(
        CandidacyInput(
            pta_right=Decimal("70"),
            pta_left=Decimal("72"),
            wrs_right_percent=50,
            wrs_left_percent=40,
            loss_type_right="sensorineural",
            loss_type_left="sensorineural",
            hearing_aid_trial_completed=True,
            imaging_clearance=True,
            communication_impact_assessed=True,
        )
    )
    assert result.cochlear_implant_eligible is True


def test_cochlear_implant_fails_without_trial() -> None:
    result = evaluate_device_candidacy(
        CandidacyInput(
            pta_right=Decimal("80"),
            pta_left=Decimal("85"),
            wrs_right_percent=30,
            wrs_left_percent=25,
            loss_type_right="sensorineural",
            loss_type_left="sensorineural",
            hearing_aid_trial_completed=False,
            imaging_clearance=True,
            communication_impact_assessed=True,
        )
    )
    assert result.cochlear_implant_eligible is False
