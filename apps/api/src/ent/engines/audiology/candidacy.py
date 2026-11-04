"""Hearing aid and cochlear implant candidacy checklist (feature spec §8.7)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ent.engines.results import CalculationResult, Flag

VERSION = "1.0.0"
CODE = "audiology.device_candidacy"
REFERENCE = (
    "Feature specification §8.7; WHO 2021 hearing impairment grades; "
    "AAO-HNS / NICE TA566 cochlear implant audiometric thresholds "
    "(# VERIFY: local reimbursement thresholds)"
)
FORMULA = (
    "HA: PTA >= 20 dB HL and audiogram documented; "
    "CI: bilateral PTA >= 70 dB HL or WRS <= 50% with trial documented"
)

HA_PTA_THRESHOLD_DB = Decimal("20")
CI_PTA_THRESHOLD_DB = Decimal("70")
CI_WRS_MAX_PERCENT = 50


@dataclass(frozen=True, slots=True)
class CandidacyInput:
    pta_right: Decimal | None
    pta_left: Decimal | None
    wrs_right_percent: int | None
    wrs_left_percent: int | None
    loss_type_right: str | None
    loss_type_left: str | None
    hearing_aid_trial_completed: bool
    imaging_clearance: bool
    communication_impact_assessed: bool


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    code: str
    met: bool


@dataclass(frozen=True, slots=True)
class CandidacyResult:
    hearing_aid_items: tuple[ChecklistItem, ...]
    cochlear_implant_items: tuple[ChecklistItem, ...]
    hearing_aid_eligible: bool
    cochlear_implant_eligible: bool
    flags: tuple[Flag, ...]


def _pta_at_least(pta: Decimal | None, threshold: Decimal) -> bool:
    return pta is not None and pta >= threshold


def _wrs_at_most(wrs: int | None, maximum: int) -> bool:
    return wrs is not None and wrs <= maximum


def evaluate_device_candidacy(data: CandidacyInput) -> CandidacyResult:
    loss_documented = bool(data.loss_type_right or data.loss_type_left) or (
        data.pta_right is not None or data.pta_left is not None
    )
    speech_recorded = (
        data.wrs_right_percent is not None or data.wrs_left_percent is not None
    )
    pta_elevated = _pta_at_least(data.pta_right, HA_PTA_THRESHOLD_DB) or _pta_at_least(
        data.pta_left, HA_PTA_THRESHOLD_DB
    )

    ha_items = (
        ChecklistItem("pta_at_least_20db", pta_elevated),
        ChecklistItem("loss_documented", loss_documented),
        ChecklistItem("speech_audiometry_recorded", speech_recorded),
        ChecklistItem(
            "communication_impact_assessed",
            data.communication_impact_assessed,
        ),
    )
    ha_eligible = all(item.met for item in ha_items)

    bilateral_severe = _pta_at_least(
        data.pta_right, CI_PTA_THRESHOLD_DB
    ) and _pta_at_least(data.pta_left, CI_PTA_THRESHOLD_DB)
    limited_speech = _wrs_at_most(
        data.wrs_right_percent, CI_WRS_MAX_PERCENT
    ) or _wrs_at_most(data.wrs_left_percent, CI_WRS_MAX_PERCENT)

    ci_items = (
        ChecklistItem("bilateral_severe_to_profound_sn_loss", bilateral_severe),
        ChecklistItem("limited_speech_recognition", limited_speech),
        ChecklistItem("hearing_aid_trial_completed", data.hearing_aid_trial_completed),
        ChecklistItem("imaging_and_medical_clearance", data.imaging_clearance),
    )
    ci_eligible = all(item.met for item in ci_items)

    flags: list[Flag] = []
    if ha_eligible:
        flags.append(Flag("hearing_aid_candidacy_met", {}))
    if ci_eligible:
        flags.append(Flag("cochlear_implant_candidacy_met", {}))

    return CandidacyResult(
        hearing_aid_items=ha_items,
        cochlear_implant_items=ci_items,
        hearing_aid_eligible=ha_eligible,
        cochlear_implant_eligible=ci_eligible,
        flags=tuple(flags),
    )


def device_candidacy_calculation(data: CandidacyInput) -> CalculationResult:
    result = evaluate_device_candidacy(data)
    summary = (
        "ci"
        if result.cochlear_implant_eligible
        else "ha" if result.hearing_aid_eligible else "none"
    )
    return CalculationResult(
        code=CODE,
        value=summary,
        unit=None,
        inputs={
            "ptaRight": str(data.pta_right) if data.pta_right is not None else "",
            "ptaLeft": str(data.pta_left) if data.pta_left is not None else "",
            "wrsRight": str(data.wrs_right_percent or ""),
            "wrsLeft": str(data.wrs_left_percent or ""),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=result.flags,
    )
