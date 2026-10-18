"""Known-answer clinical tests for the recall protocol resolver (P3-08).

Reference: EntShifa Feature Specification §15.3 and Appendix C (2026).
"""

from __future__ import annotations

from datetime import date

import pytest

from ent.engines.recalls.protocol_resolver import (
    CODE,
    VERSION,
    DeviceStateSpec,
    OpenRecallSpec,
    ProcedureTriggerContext,
    ProtocolRuleSpec,
    add_days,
    add_months,
    evaluate_condition,
    is_stop_condition_met,
    resolve_protocol,
)
from ent.engines.registry import registered_calculators


def _ventilation_tube_rules() -> tuple[ProtocolRuleSpec, ...]:
    return (
        ProtocolRuleSpec(
            protocol_id=1,
            protocol_code="PROT.VENTILATION_TUBE",
            rule_id=101,
            sequence=1,
            offset_days=21,
            window_days=7,
            action_type="visit",
            action_config={
                "completedByProcedureCodes": [
                    "PROC.OTOSCOPY",
                    "PROC.OTOMICROSCOPY",
                ],
                "cancelledByProcedureCodes": ["PROC.TUBE_REMOVAL"],
            },
            condition=None,
            label_key="otology_tube_patency",
        ),
        ProtocolRuleSpec(
            protocol_id=1,
            protocol_code="PROT.VENTILATION_TUBE",
            rule_id=102,
            sequence=2,
            offset_days=90,
            window_days=14,
            action_type="test",
            action_config={
                "test": "audiogram",
                "cancelledByProcedureCodes": ["PROC.TUBE_REMOVAL"],
            },
            condition={"field": "has_preop_hearing_loss", "eq": True},
            label_key="otology_tube_audiogram",
        ),
        ProtocolRuleSpec(
            protocol_id=1,
            protocol_code="PROT.VENTILATION_TUBE",
            rule_id=103,
            sequence=3,
            offset_days=180,
            window_days=30,
            action_type="visit",
            action_config={
                "offsetMonths": 6,
                "repeatEveryMonths": 6,
                "stopCondition": {
                    "deviceType": "ventilation_tube",
                    "closedStatuses": ["extruded", "removed"],
                },
                "completedByProcedureCodes": [
                    "PROC.OTOSCOPY",
                    "PROC.OTOMICROSCOPY",
                ],
                "cancelledByProcedureCodes": ["PROC.TUBE_REMOVAL"],
            },
            condition=None,
            label_key="otology_tube_check",
        ),
    )


@pytest.mark.clinical
def test_registry_lists_protocol_resolver() -> None:
    match = [item for item in registered_calculators() if item.code == CODE]
    assert len(match) == 1
    assert match[0].version == VERSION
    assert match[0].unit == "recall"


@pytest.mark.clinical
def test_ventilation_tube_without_preop_hearing_loss_schedules_patency_and_6m_check() -> (
    None
):
    # Appendix C: Ventilation tubes -> visit 3-4 weeks (21d + 7d); then every 6 months until extrusion.
    res = resolve_protocol(
        rules=_ventilation_tube_rules(),
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.VENTILATION_TUBE",
            performed_on=date(2026, 6, 2),
            laterality="right",
            attributes={"has_preop_hearing_loss": False},
            devices=(
                DeviceStateSpec(
                    device_type="ventilation_tube",
                    laterality="right",
                    status="in_place",
                ),
            ),
        ),
    )
    assert res.calculation.code == CODE
    assert res.calculation.version == VERSION
    assert res.calculation.value == "2"
    assert [item.reason_key for item in res.planned] == [
        "otology_tube_patency",
        "otology_tube_check",
    ]
    assert res.planned[0].due_on == date(2026, 6, 23)
    assert res.planned[0].window_days == 7
    assert res.planned[0].is_repeating is False
    assert res.planned[1].due_on == date(2026, 12, 2)
    assert res.planned[1].window_days == 30
    assert res.planned[1].is_repeating is True
    assert any(flag.code == "condition_skipped" for flag in res.calculation.flags)


@pytest.mark.clinical
def test_ventilation_tube_with_preop_hearing_loss_includes_90d_audiogram() -> None:
    # Appendix C: audiogram at 3 months (90d + 14d window) if hearing loss pre-op.
    res = resolve_protocol(
        rules=_ventilation_tube_rules(),
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.VENTILATION_TUBE",
            performed_on=date(2026, 6, 2),
            laterality="left",
            attributes={"has_preop_hearing_loss": True},
            devices=(
                DeviceStateSpec(
                    device_type="ventilation_tube",
                    laterality="left",
                    status="in_place",
                ),
            ),
        ),
    )
    assert res.calculation.value == "3"
    assert [item.reason_key for item in res.planned] == [
        "otology_tube_patency",
        "otology_tube_audiogram",
        "otology_tube_check",
    ]
    assert res.planned[1].due_on == date(2026, 8, 31)
    assert res.planned[1].window_days == 14
    assert res.planned[1].action_type == "test"
    assert res.planned[1].action_config["test"] == "audiogram"


@pytest.mark.clinical
def test_epistaxis_pack_vs_cautery_condition_evaluation() -> None:
    # Appendix C: Epistaxis pack removal 48-72h; cautery creates no recall.
    rule = ProtocolRuleSpec(
        protocol_id=2,
        protocol_code="PROT.EPISTAXIS_PACK",
        rule_id=201,
        sequence=1,
        offset_days=2,
        window_days=1,
        action_type="visit",
        action_config={"dueDateField": "removal_due_date"},
        condition={
            "field": "method",
            "in": ["anterior_pack", "posterior_pack", "balloon"],
        },
        label_key="office_pack_removal",
    )
    cautery = resolve_protocol(
        rules=(rule,),
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.EPISTAXIS_MANAGEMENT",
            performed_on=date(2026, 6, 2),
            laterality="right",
            attributes={"method": "silver_nitrate"},
        ),
    )
    assert cautery.planned == ()
    assert cautery.calculation.value == "0"

    packed_default = resolve_protocol(
        rules=(rule,),
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.EPISTAXIS_MANAGEMENT",
            performed_on=date(2026, 6, 2),
            laterality="right",
            attributes={"method": "anterior_pack"},
        ),
    )
    assert len(packed_default.planned) == 1
    assert packed_default.planned[0].due_on == date(2026, 6, 4)
    assert packed_default.planned[0].window_days == 1

    packed_override_date = resolve_protocol(
        rules=(rule,),
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.EPISTAXIS_MANAGEMENT",
            performed_on=date(2026, 6, 2),
            laterality="right",
            attributes={
                "method": "posterior_pack",
                "removal_due_date": "2026-06-05",
            },
        ),
    )
    assert packed_override_date.planned[0].due_on == date(2026, 6, 5)


@pytest.mark.clinical
def test_completing_repeating_tube_check_schedules_next_6m_until_extruded() -> None:
    rules = _ventilation_tube_rules()
    open_check = OpenRecallSpec(
        recall_id=500,
        protocol_id=1,
        protocol_rule_id=103,
        reason_key="otology_tube_check",
        laterality="right",
        due_on=date(2026, 12, 2),
        window_days=30,
        action_type="visit",
        action_config=rules[2].action_config,
    )
    # 1. Tube still in_place: otoscopy closes recall #500 and plans next 6-month recall
    active_res = resolve_protocol(
        rules=(),
        transition_rules=rules,
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.OTOSCOPY",
            performed_on=date(2026, 12, 5),
            laterality="right",
            attributes={},
            devices=(
                DeviceStateSpec(
                    device_type="ventilation_tube",
                    laterality="right",
                    status="in_place",
                ),
            ),
        ),
        open_recalls=(open_check,),
    )
    assert len(active_res.transitions) == 1
    assert active_res.transitions[0].recall_id == 500
    assert active_res.transitions[0].new_status == "done"
    assert len(active_res.planned) == 1
    assert active_res.planned[0].reason_key == "otology_tube_check"
    assert active_res.planned[0].due_on == date(2027, 6, 5)

    # 2. Tube extruded: otoscopy closes recall #500 and terminates repeating series
    stopped_res = resolve_protocol(
        rules=(),
        transition_rules=rules,
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.OTOSCOPY",
            performed_on=date(2026, 12, 5),
            laterality="right",
            attributes={},
            devices=(
                DeviceStateSpec(
                    device_type="ventilation_tube",
                    laterality="right",
                    status="extruded",
                ),
            ),
        ),
        open_recalls=(open_check,),
    )
    assert len(stopped_res.transitions) == 1
    assert stopped_res.transitions[0].new_status == "done"
    assert stopped_res.planned == ()
    assert any(
        f.code == "stop_condition_terminated" for f in stopped_res.calculation.flags
    )


@pytest.mark.clinical
def test_edge_branches_for_conditions_dates_and_transitions() -> None:
    # Month-end clamping (Jan 31 + 1 month -> Feb 28)
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_days(date(2026, 6, 1), 10) == date(2026, 6, 11)

    # Combinators and operators in evaluate_condition
    assert evaluate_condition(None, {}) is True
    assert (
        evaluate_condition(
            {
                "all": [
                    {"field": "a", "eq": 1},
                    {"field": "b", "not_in": ["x", "y"]},
                ]
            },
            {"a": 1, "b": "z"},
        )
        is True
    )
    assert (
        evaluate_condition(
            {
                "any": [
                    {"field": "c", "exists": True},
                    {"field": "d", "eq": "ok"},
                ]
            },
            {"c": "present"},
        )
        is True
    )
    assert evaluate_condition({"unknown": 1}, {}) is False
    assert evaluate_condition({"field": "x"}, {"x": 1}) is False

    # Stop conditions: empty / non-mapping / attributeTrue / requireActiveDevice
    assert (
        is_stop_condition_met(None, laterality="right", devices=(), attributes={})
        is False
    )
    assert (
        is_stop_condition_met(
            {"stopCondition": "invalid"},
            laterality="right",
            devices=(),
            attributes={},
        )
        is False
    )
    assert (
        is_stop_condition_met(
            {"stopCondition": {"other": 1}},
            laterality="right",
            devices=(),
            attributes={},
        )
        is False
    )
    assert (
        is_stop_condition_met(
            {"stopCondition": {"attributeTrue": "extruded"}},
            laterality="right",
            devices=(),
            attributes={"extruded": True},
        )
        is True
    )
    assert (
        is_stop_condition_met(
            {
                "stopCondition": {
                    "deviceType": "ventilation_tube",
                    "closedStatuses": ["removed"],
                    "requireActiveDevice": True,
                }
            },
            laterality="right",
            devices=(),
            attributes={},
        )
        is True
    )

    # Rule with requireDueDateField when missing date, rule already stopped on trigger,
    # and repeatEveryDays / custom offset_days
    rules = (
        ProtocolRuleSpec(
            protocol_id=3,
            protocol_code="PROT.TEST",
            rule_id=301,
            sequence=1,
            offset_days=7,
            window_days=2,
            action_type="visit",
            action_config={
                "dueDateField": "missing_date",
                "requireDueDateField": True,
            },
            condition=None,
            label_key="missing_date_rule",
        ),
        ProtocolRuleSpec(
            protocol_id=3,
            protocol_code="PROT.TEST",
            rule_id=302,
            sequence=2,
            offset_days=10,
            window_days=2,
            action_type="visit",
            action_config={
                "dueDateField": "explicit_date",
                "stopCondition": {"attributeTrue": "stopped"},
            },
            condition=None,
            label_key="stopped_rule",
        ),
        ProtocolRuleSpec(
            protocol_id=3,
            protocol_code="PROT.TEST",
            rule_id=303,
            sequence=3,
            offset_days=45,
            window_days=5,
            action_type="visit",
            action_config={
                "dueDateField": "date_obj",
                "repeatEveryDays": 45,
                "completedByProcedureCodes": ["PROC.FOLLOWUP"],
                "cancelledByProcedureCodes": ["PROC.CANCEL"],
            },
            condition=None,
            label_key="daily_repeat_rule",
        ),
        ProtocolRuleSpec(
            protocol_id=3,
            protocol_code="PROT.TEST",
            rule_id=304,
            sequence=4,
            offset_days=200,
            window_days=5,
            action_type="visit",
            action_config={
                "offsetMonths": 6,
                "repeatEveryMonths": 6,
                "completedByProcedureCodes": ["PROC.MONTH_CUSTOM"],
            },
            condition=None,
            label_key="custom_days_override_rule",
        ),
        ProtocolRuleSpec(
            protocol_id=3,
            protocol_code="PROT.TEST",
            rule_id=305,
            sequence=5,
            offset_days=14,
            window_days=3,
            action_type="visit",
            action_config=None,
            condition=None,
            label_key="plain_rule_no_config",
        ),
    )
    res = resolve_protocol(
        rules=rules,
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.TEST",
            performed_on=date(2026, 6, 2),
            laterality="bilateral",
            attributes={
                "stopped": True,
                "date_obj": date(2026, 6, 15),
            },
        ),
    )
    assert len(res.planned) == 3
    assert res.planned[0].due_on == date(2026, 6, 15)
    # Custom offset_days != offsetMonths * 30 uses offset_days (200 days)
    assert res.planned[1].due_on == date(2026, 12, 19)
    assert res.planned[2].due_on == date(2026, 6, 16)

    # Open recall transitions: laterality mismatch skipped, cancel transition,
    # repeatEveryDays next due, custom offset_days fallback in _next_repeat_due,
    # and duplicate repeating open recalls deduplicated
    open_recalls = (
        OpenRecallSpec(
            recall_id=1,
            protocol_id=3,
            protocol_rule_id=303,
            reason_key="daily_repeat_rule",
            laterality="left",
            due_on=date(2026, 7, 1),
            window_days=5,
            action_type="visit",
            action_config=rules[2].action_config,
        ),
        OpenRecallSpec(
            recall_id=2,
            protocol_id=3,
            protocol_rule_id=303,
            reason_key="daily_repeat_rule",
            laterality="right",
            due_on=date(2026, 7, 1),
            window_days=5,
            action_type="visit",
            action_config=rules[2].action_config,
        ),
        OpenRecallSpec(
            recall_id=22,
            protocol_id=3,
            protocol_rule_id=303,
            reason_key="daily_repeat_rule",
            laterality="right",
            due_on=date(2026, 7, 5),
            window_days=5,
            action_type="visit",
            action_config=rules[2].action_config,
        ),
        OpenRecallSpec(
            recall_id=3,
            protocol_id=None,
            protocol_rule_id=None,
            reason_key="custom_days_override_rule",
            laterality="na",
            due_on=date(2026, 7, 1),
            window_days=5,
            action_type="visit",
            action_config=None,
        ),
        OpenRecallSpec(
            recall_id=4,
            protocol_id=None,
            protocol_rule_id=None,
            reason_key="untracked_reason",
            laterality="right",
            due_on=date(2026, 7, 1),
            window_days=5,
            action_type="visit",
            action_config=None,
        ),
    )
    cancel_res = resolve_protocol(
        rules=(),
        transition_rules=rules,
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.CANCEL",
            performed_on=date(2026, 7, 2),
            laterality="right",
            attributes={},
        ),
        open_recalls=open_recalls,
    )
    assert len(cancel_res.transitions) == 2
    assert cancel_res.transitions[0].recall_id == 2
    assert cancel_res.transitions[0].new_status == "cancelled"

    followup_res = resolve_protocol(
        rules=(),
        transition_rules=rules,
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.FOLLOWUP",
            performed_on=date(2026, 7, 2),
            laterality="right",
            attributes={},
        ),
        open_recalls=open_recalls,
        closing_rules={
            "PROC.FOLLOWUP": (
                "custom_days_override_rule",
                "plain_rule_no_config",
            )
        },
    )
    assert len(followup_res.transitions) == 3
    assert len(followup_res.planned) == 2
    assert followup_res.planned[0].due_on == date(2026, 8, 16)
    assert followup_res.planned[1].due_on == date(2027, 1, 18)

    # Also cover non-repeating rule closed via closing_rules
    non_rep_close = resolve_protocol(
        rules=(),
        transition_rules=rules,
        context=ProcedureTriggerContext(
            procedure_concept_code="PROC.PLAIN_CLOSE",
            performed_on=date(2026, 7, 2),
            laterality="right",
            attributes={},
        ),
        open_recalls=(
            OpenRecallSpec(
                recall_id=99,
                protocol_id=3,
                protocol_rule_id=305,
                reason_key="plain_rule_no_config",
                laterality="right",
                due_on=date(2026, 7, 1),
                window_days=3,
                action_type="visit",
                action_config=None,
            ),
        ),
        closing_rules={"PROC.PLAIN_CLOSE": ("plain_rule_no_config",)},
    )
    assert len(non_rep_close.transitions) == 1
    assert non_rep_close.transitions[0].new_status == "done"
    assert len(non_rep_close.planned) == 0
