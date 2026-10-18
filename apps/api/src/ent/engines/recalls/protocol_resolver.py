"""Pure recall protocol resolver (architecture §4, §8, §25.15 / P3-08).

Evaluates database-driven protocol rules, conditions, repeating series, stop
conditions, and automatic recall completion/cancellation without I/O.
"""

from __future__ import annotations

import calendar
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from ent.engines.results import CalculationResult, Flag

CODE = "recalls.protocol_resolver"
VERSION = "1.0.0"
REFERENCE = "EntShifa Feature Specification §15.3 and Appendix C (2026)"
FORMULA = (
    "due_on = override_date | add_months(performed_on, repeat_months) "
    "| performed_on + offset_days"
)


@dataclass(frozen=True, slots=True)
class ProtocolRuleSpec:
    """One database protocol rule passed into the pure engine."""

    protocol_id: int
    protocol_code: str
    rule_id: int
    sequence: int
    offset_days: int
    window_days: int
    action_type: str
    action_config: Mapping[str, Any] | None
    condition: Mapping[str, Any] | None
    label_key: str


@dataclass(frozen=True, slots=True)
class DeviceStateSpec:
    """State of a tracked ear device for stop-condition evaluation."""

    device_type: str
    laterality: str
    status: str


@dataclass(frozen=True, slots=True)
class ProcedureTriggerContext:
    """Facts about a performed procedure used to evaluate protocol rules."""

    procedure_concept_code: str
    performed_on: date
    laterality: str
    attributes: Mapping[str, Any]
    devices: tuple[DeviceStateSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class PlannedProtocolRecall:
    """One recall row to materialize from a matched protocol rule."""

    protocol_id: int
    protocol_rule_id: int
    protocol_code: str
    sequence: int
    reason_key: str
    due_on: date
    window_days: int
    action_type: str
    action_config: dict[str, Any]
    laterality: str
    is_repeating: bool


@dataclass(frozen=True, slots=True)
class OpenRecallSpec:
    """An existing open recall on the patient chart."""

    recall_id: int
    protocol_id: int | None
    protocol_rule_id: int | None
    reason_key: str | None
    laterality: str | None
    due_on: date
    window_days: int
    action_type: str
    action_config: Mapping[str, Any] | None


@dataclass(frozen=True, slots=True)
class RecallTransition:
    """Automatic status change on an open recall when an expected event happens."""

    recall_id: int
    new_status: str
    cancelled_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ProtocolResolutionResult:
    """Output of resolving protocol rules for a procedure."""

    planned: tuple[PlannedProtocolRecall, ...]
    transitions: tuple[RecallTransition, ...]
    calculation: CalculationResult


def add_months(value: date, months: int) -> date:
    """Move a clinic-local date by a whole number of months, clamping the day."""

    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_days(value: date, days: int) -> date:
    """Move a clinic-local date by a number of calendar days."""

    return value + timedelta(days=days)


def evaluate_condition(
    condition: Mapping[str, Any] | None,
    attributes: Mapping[str, Any],
) -> bool:
    """Evaluate a declarative JSON rule condition against procedure attributes."""

    if not condition:
        return True
    if "all" in condition:
        items = condition["all"]
        return isinstance(items, Sequence) and all(
            isinstance(item, Mapping) and evaluate_condition(item, attributes)
            for item in items
        )
    if "any" in condition:
        items = condition["any"]
        return isinstance(items, Sequence) and any(
            isinstance(item, Mapping) and evaluate_condition(item, attributes)
            for item in items
        )
    field_name = condition.get("field")
    if not isinstance(field_name, str):
        return False
    actual = attributes.get(field_name)
    if "exists" in condition:
        wanted = bool(condition["exists"])
        return (actual is not None) is wanted
    if "eq" in condition:
        return bool(actual == condition["eq"])
    if "in" in condition:
        options = condition["in"]
        return isinstance(options, Sequence) and actual in options
    if "not_in" in condition:
        options = condition["not_in"]
        return isinstance(options, Sequence) and actual not in options
    return False


def is_stop_condition_met(
    action_config: Mapping[str, Any] | None,
    *,
    laterality: str,
    devices: Sequence[DeviceStateSpec],
    attributes: Mapping[str, Any],
) -> bool:
    """Return True when a repeating rule's explicit stop condition is met."""

    if not action_config:
        return False
    stop = action_config.get("stopCondition")
    if not isinstance(stop, Mapping):
        return False
    stop_flag = stop.get("attributeTrue")
    if isinstance(stop_flag, str) and bool(attributes.get(stop_flag)) is True:
        return True
    device_type = stop.get("deviceType")
    closed_statuses = stop.get("closedStatuses")
    if isinstance(device_type, str) and isinstance(closed_statuses, Sequence):
        matching = [
            dev
            for dev in devices
            if dev.device_type == device_type
            and (laterality in ("na", "bilateral") or dev.laterality == laterality)
        ]
        if matching and all(dev.status in closed_statuses for dev in matching):
            return True
        if bool(stop.get("requireActiveDevice")) and not matching:
            return True
    return False


def _resolve_due_on(
    rule: ProtocolRuleSpec,
    context: ProcedureTriggerContext,
) -> date | None:
    config = rule.action_config or {}
    due_field = config.get("dueDateField")
    if isinstance(due_field, str):
        raw = context.attributes.get(due_field)
        if isinstance(raw, date):
            return raw
        if isinstance(raw, str) and raw:
            return date.fromisoformat(raw)
        if bool(config.get("requireDueDateField")):
            return None
    offset_months = config.get("offsetMonths")
    if (
        isinstance(offset_months, int)
        and not isinstance(offset_months, bool)
        and offset_months > 0
        and rule.offset_days == offset_months * 30
    ):
        return add_months(context.performed_on, offset_months)
    return add_days(context.performed_on, rule.offset_days)


def _is_repeating(action_config: Mapping[str, Any] | None) -> bool:
    if not action_config:
        return False
    repeat_days = action_config.get("repeatEveryDays")
    repeat_months = action_config.get("repeatEveryMonths")
    return bool(
        (isinstance(repeat_days, int) and repeat_days > 0)
        or (isinstance(repeat_months, int) and repeat_months > 0)
    )


def _laterality_matches(recall_side: str | None, event_side: str) -> bool:
    if (
        recall_side is None
        or recall_side in ("na", "bilateral")
        or event_side in ("na", "bilateral")
    ):
        return True
    return recall_side == event_side


def resolve_protocol(
    *,
    rules: Sequence[ProtocolRuleSpec],
    context: ProcedureTriggerContext,
    open_recalls: Sequence[OpenRecallSpec] = (),
    closing_rules: Mapping[str, Sequence[str]] | None = None,
    cancelling_rules: Mapping[str, Sequence[str]] | None = None,
    transition_rules: Sequence[ProtocolRuleSpec] = (),
) -> ProtocolResolutionResult:
    """Resolve planned recalls and open-recall transitions for a procedure event."""

    ordered = sorted(rules, key=lambda item: (item.protocol_code, item.sequence))
    planned: list[PlannedProtocolRecall] = []
    flags: list[Flag] = []

    for rule in ordered:
        if not evaluate_condition(rule.condition, context.attributes):
            flags.append(
                Flag(
                    code="condition_skipped",
                    detail={
                        "protocol": rule.protocol_code,
                        "rule": rule.label_key,
                    },
                )
            )
            continue
        if is_stop_condition_met(
            rule.action_config,
            laterality=context.laterality,
            devices=context.devices,
            attributes=context.attributes,
        ):
            flags.append(
                Flag(
                    code="stop_condition_terminated",
                    detail={
                        "protocol": rule.protocol_code,
                        "rule": rule.label_key,
                    },
                )
            )
            continue
        due_on = _resolve_due_on(rule, context)
        if due_on is None:
            flags.append(
                Flag(
                    code="due_date_missing",
                    detail={
                        "protocol": rule.protocol_code,
                        "rule": rule.label_key,
                    },
                )
            )
            continue
        merged_config: dict[str, Any] = {
            "reasonKey": rule.label_key,
            **(rule.action_config or {}),
        }
        repeating = _is_repeating(rule.action_config)
        planned.append(
            PlannedProtocolRecall(
                protocol_id=rule.protocol_id,
                protocol_rule_id=rule.rule_id,
                protocol_code=rule.protocol_code,
                sequence=rule.sequence,
                reason_key=rule.label_key,
                due_on=due_on,
                window_days=rule.window_days,
                action_type=rule.action_type,
                action_config=merged_config,
                laterality=context.laterality,
                is_repeating=repeating,
            )
        )

    transitions, repeat_followups = _resolve_open_transitions(
        open_recalls=open_recalls,
        rules=tuple(transition_rules) if transition_rules else ordered,
        context=context,
        already_planned_keys={(item.reason_key, item.laterality) for item in planned},
        closing_map=closing_rules or {},
        cancelling_map=cancelling_rules or {},
        flags=flags,
    )
    planned.extend(repeat_followups)

    calculation = CalculationResult(
        code=CODE,
        value=str(len(planned)),
        unit="recall",
        inputs={
            "procedureConceptCode": context.procedure_concept_code,
            "performedOn": context.performed_on.isoformat(),
            "laterality": context.laterality,
            "rulesEvaluated": str(len(ordered)),
        },
        formula=FORMULA,
        version=VERSION,
        reference=REFERENCE,
        flags=tuple(flags),
    )
    return ProtocolResolutionResult(
        planned=tuple(planned),
        transitions=tuple(transitions),
        calculation=calculation,
    )


def _resolve_open_transitions(
    *,
    open_recalls: Sequence[OpenRecallSpec],
    rules: Sequence[ProtocolRuleSpec],
    context: ProcedureTriggerContext,
    already_planned_keys: set[tuple[str, str]],
    closing_map: Mapping[str, Sequence[str]],
    cancelling_map: Mapping[str, Sequence[str]],
    flags: list[Flag],
) -> tuple[list[RecallTransition], list[PlannedProtocolRecall]]:
    transitions: list[RecallTransition] = []
    repeat_followups: list[PlannedProtocolRecall] = []
    close_keys = set(closing_map.get(context.procedure_concept_code, ()))
    cancel_keys = set(cancelling_map.get(context.procedure_concept_code, ()))
    rule_by_id = {rule.rule_id: rule for rule in rules}
    rule_by_label = {rule.label_key: rule for rule in rules}

    for open_recall in open_recalls:
        reason = open_recall.reason_key or ""
        if not _laterality_matches(open_recall.laterality, context.laterality):
            continue

        rule = (
            rule_by_id.get(open_recall.protocol_rule_id)
            if open_recall.protocol_rule_id is not None
            else None
        ) or rule_by_label.get(reason)

        config = (
            open_recall.action_config or (rule.action_config if rule else None) or {}
        )
        rule_close_codes = config.get("completedByProcedureCodes")
        rule_cancel_codes = config.get("cancelledByProcedureCodes")
        completed_by_rule = (
            isinstance(rule_close_codes, Sequence)
            and context.procedure_concept_code in rule_close_codes
        )
        cancelled_by_rule = (
            isinstance(rule_cancel_codes, Sequence)
            and context.procedure_concept_code in rule_cancel_codes
        )

        if reason in cancel_keys or cancelled_by_rule:
            transitions.append(
                RecallTransition(
                    recall_id=open_recall.recall_id,
                    new_status="cancelled",
                    cancelled_reason="protocol_stop_condition",
                )
            )
            flags.append(
                Flag(
                    code="recall_cancelled",
                    detail={"reasonKey": reason},
                )
            )
            continue

        if reason in close_keys or completed_by_rule:
            transitions.append(
                RecallTransition(
                    recall_id=open_recall.recall_id,
                    new_status="done",
                )
            )
            flags.append(
                Flag(
                    code="recall_completed",
                    detail={"reasonKey": reason},
                )
            )
            if rule is not None and _is_repeating(rule.action_config):
                target_side = open_recall.laterality or context.laterality
                if is_stop_condition_met(
                    rule.action_config,
                    laterality=target_side,
                    devices=context.devices,
                    attributes=context.attributes,
                ):
                    flags.append(
                        Flag(
                            code="stop_condition_terminated",
                            detail={
                                "protocol": rule.protocol_code,
                                "rule": rule.label_key,
                            },
                        )
                    )
                elif (rule.label_key, target_side) not in already_planned_keys:
                    next_due = _next_repeat_due(rule, context.performed_on)
                    merged_cfg: dict[str, Any] = {
                        "reasonKey": rule.label_key,
                        **(rule.action_config or {}),
                    }
                    repeat_followups.append(
                        PlannedProtocolRecall(
                            protocol_id=rule.protocol_id,
                            protocol_rule_id=rule.rule_id,
                            protocol_code=rule.protocol_code,
                            sequence=rule.sequence,
                            reason_key=rule.label_key,
                            due_on=next_due,
                            window_days=rule.window_days,
                            action_type=rule.action_type,
                            action_config=merged_cfg,
                            laterality=target_side,
                            is_repeating=True,
                        )
                    )
                    already_planned_keys.add((rule.label_key, target_side))

    return transitions, repeat_followups


def _next_repeat_due(rule: ProtocolRuleSpec, performed_on: date) -> date:
    config = rule.action_config or {}
    repeat_months = config.get("repeatEveryMonths")
    if (
        isinstance(repeat_months, int)
        and not isinstance(repeat_months, bool)
        and repeat_months > 0
        and rule.offset_days == repeat_months * 30
    ):
        return add_months(performed_on, repeat_months)
    repeat_days = config.get("repeatEveryDays")
    if (
        isinstance(repeat_days, int)
        and not isinstance(repeat_days, bool)
        and repeat_days > 0
    ):
        return add_days(performed_on, repeat_days)
    return add_days(performed_on, rule.offset_days)
