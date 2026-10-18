"""Recall protocol orchestration and ProcedurePerformed event handler (P3-08).

Loads database protocol rules, maps clinical procedure/device state into the
pure ``ent.engines.recalls.protocol_resolver`` engine, and persists recalls
with ``protocol_id`` and ``protocol_rule_id`` provenance.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session_factory
from ent.core.events.events import DomainEvent
from ent.core.utils.ids import new_ulid
from ent.engines.recalls.protocol_resolver import (
    DeviceStateSpec,
    OpenRecallSpec,
    PlannedProtocolRecall,
    ProcedureTriggerContext,
    ProtocolRuleSpec,
    is_stop_condition_met,
    resolve_protocol,
)
from ent.features.clinics.repository import ClinicRepository
from ent.features.otology.models import EarDevice, OfficeProcedure
from ent.features.otology.repository import (
    EarDeviceRepository,
    OfficeProcedureRepository,
    ProcedureRecallRepository,
)
from ent.features.procedures.models import ProcedureRecord
from ent.features.procedures.repository import ProcedureRecordRepository
from ent.features.recalls.constants import RECALL_LATERALITIES
from ent.features.recalls.dates import clinic_local_date
from ent.features.recalls.models import Protocol, Recall
from ent.features.recalls.repository import ProtocolRepository
from ent.seeds.protocols import SYSTEM_PROTOCOLS, seed_protocols

_CODE_TO_PROTOCOL_CODES: dict[str, tuple[str, ...]] = {}
for _spec in SYSTEM_PROTOCOLS:
    for _concept_code in _spec.trigger_concept_codes:
        _CODE_TO_PROTOCOL_CODES[_concept_code] = (
            *_CODE_TO_PROTOCOL_CODES.get(_concept_code, ()),
            _spec.code,
        )


async def ensure_protocols_for_clinic(
    session: AsyncSession,
    *,
    clinic_id: int,
) -> list[Protocol]:
    """Return effective active procedure protocols for ``clinic_id``, seeding defaults if empty."""

    repo = ProtocolRepository(session, clinic_id=clinic_id)
    protocols = await repo.list_effective(trigger_type="procedure", active_only=False)
    if not protocols:
        await seed_protocols(session)
        protocols = await repo.list_effective(
            trigger_type="procedure", active_only=False
        )
    return [row for row in protocols if row.is_active]


def _rule_specs_for_protocols(
    protocols: list[Protocol],
    *,
    procedure_concept_id: int,
    procedure_concept_code: str,
) -> list[ProtocolRuleSpec]:
    matched_codes = set(_CODE_TO_PROTOCOL_CODES.get(procedure_concept_code, ()))
    specs: list[ProtocolRuleSpec] = []
    for proto in protocols:
        trigger_ids = proto.trigger_concept_ids or []
        if procedure_concept_id not in trigger_ids and proto.code not in matched_codes:
            continue
        for rule in proto.rules:
            if rule.deleted_at is not None:
                continue
            specs.append(
                ProtocolRuleSpec(
                    protocol_id=int(proto.id),
                    protocol_code=proto.code,
                    rule_id=int(rule.id),
                    sequence=int(rule.sequence),
                    offset_days=int(rule.offset_days),
                    window_days=int(rule.window_days),
                    action_type=rule.action_type,
                    action_config=(
                        dict(rule.action_config)
                        if rule.action_config is not None
                        else None
                    ),
                    condition=(
                        dict(rule.condition) if rule.condition is not None else None
                    ),
                    label_key=rule.label_key,
                )
            )
    return specs


def _all_rule_specs(protocols: list[Protocol]) -> list[ProtocolRuleSpec]:
    specs: list[ProtocolRuleSpec] = []
    for proto in protocols:
        for rule in proto.rules:
            if rule.deleted_at is not None:
                continue
            specs.append(
                ProtocolRuleSpec(
                    protocol_id=int(proto.id),
                    protocol_code=proto.code,
                    rule_id=int(rule.id),
                    sequence=int(rule.sequence),
                    offset_days=int(rule.offset_days),
                    window_days=int(rule.window_days),
                    action_type=rule.action_type,
                    action_config=(
                        dict(rule.action_config)
                        if rule.action_config is not None
                        else None
                    ),
                    condition=(
                        dict(rule.condition) if rule.condition is not None else None
                    ),
                    label_key=rule.label_key,
                )
            )
    return specs


def extract_procedure_attributes(
    *,
    office: OfficeProcedure | None,
    extra_attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize stored ``OfficeProcedure`` JSON and dates into engine attributes."""

    attrs: dict[str, Any] = {}
    if office is not None:
        raw = dict(office.payload or {})
        attrs.update(raw)
        if office.removal_due_date is not None:
            attrs["removal_due_date"] = office.removal_due_date
        if office.result_due_date is not None:
            attrs["result_due_date"] = office.result_due_date
        # Normalize camelCase JSON keys from short office forms
        if "packRemovalDate" in raw and "removal_due_date" not in attrs:
            attrs["removal_due_date"] = raw["packRemovalDate"]
        if "splintRemovalDate" in raw and "removal_due_date" not in attrs:
            attrs["removal_due_date"] = raw["splintRemovalDate"]
        if "resultDueDate" in raw and "result_due_date" not in attrs:
            attrs["result_due_date"] = raw["resultDueDate"]
        if "followUpDate" in raw and "follow_up_date" not in attrs:
            attrs["follow_up_date"] = raw["followUpDate"]
        if "hasPreopHearingLoss" in raw and "has_preop_hearing_loss" not in attrs:
            attrs["has_preop_hearing_loss"] = bool(raw["hasPreopHearingLoss"])
        subtype = office.subtype
        if subtype == "wax_removal":
            canal_cond = raw.get("canal_condition") or raw.get("canalCondition")
            attrs["canal_traumatized"] = canal_cond == "traumatized"
        elif subtype == "foreign_body":
            trauma = raw.get("trauma")
            attrs["canal_traumatized"] = trauma is not None and trauma != "none"
    if extra_attributes:
        attrs.update(extra_attributes)
    return attrs


async def resolve_and_sync_procedure_recalls(
    session: AsyncSession,
    *,
    clinic_id: int,
    user_id: int | None,
    procedure: ProcedureRecord,
    procedure_concept_code: str,
    performed_on: date,
    office: OfficeProcedure | None,
    extra_attributes: dict[str, Any] | None = None,
    superseded_reason: str = "protocol_superseded",
    replace_existing_for_source: bool = True,
    apply_completion_transitions: bool = False,
) -> list[PlannedProtocolRecall]:
    """Evaluate protocol rules for ``procedure`` and synchronize its recall rows."""

    protocols = await ensure_protocols_for_clinic(session, clinic_id=clinic_id)
    trigger_rules = _rule_specs_for_protocols(
        protocols,
        procedure_concept_id=int(procedure.procedure_concept_id),
        procedure_concept_code=procedure_concept_code,
    )
    all_rules = _all_rule_specs(protocols)

    devices_repo = EarDeviceRepository(session, clinic_id=clinic_id)
    patient_devices = (
        (
            await session.execute(
                select(EarDevice).where(
                    EarDevice.clinic_id == clinic_id,
                    EarDevice.patient_id == int(procedure.patient_id),
                    EarDevice.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    device_specs = tuple(
        DeviceStateSpec(
            device_type=row.device_type,
            laterality=row.laterality,
            status=row.status,
        )
        for row in patient_devices
    )

    recall_repo = ProcedureRecallRepository(session, clinic_id=clinic_id)
    existing_for_source = await recall_repo.list_for_procedure(int(procedure.id))
    open_patient_recalls = await recall_repo.list_open_for_patient(
        int(procedure.patient_id)
    )
    source_recall_ids = {int(r.id) for r in existing_for_source}

    open_specs: list[OpenRecallSpec] = []
    if apply_completion_transitions:
        for row in open_patient_recalls:
            if int(row.id) in source_recall_ids:
                continue
            open_specs.append(
                OpenRecallSpec(
                    recall_id=int(row.id),
                    protocol_id=int(row.protocol_id) if row.protocol_id else None,
                    protocol_rule_id=(
                        int(row.protocol_rule_id) if row.protocol_rule_id else None
                    ),
                    reason_key=row.reason_key,
                    laterality=row.laterality,
                    due_on=row.due_on,
                    window_days=int(row.window_days),
                    action_type=row.action_type,
                    action_config=row.action_config,
                )
            )

    side = procedure.laterality if procedure.laterality in RECALL_LATERALITIES else "na"
    attrs = extract_procedure_attributes(
        office=office,
        extra_attributes=extra_attributes,
    )
    context = ProcedureTriggerContext(
        procedure_concept_code=procedure_concept_code,
        performed_on=performed_on,
        laterality=side,
        attributes=attrs,
        devices=device_specs,
    )

    # Evaluate trigger rules and open-recall transitions in a single pure call
    resolution = resolve_protocol(
        rules=trigger_rules,
        transition_rules=all_rules,
        context=context,
        open_recalls=open_specs,
    )
    planned = list(resolution.planned)

    if apply_completion_transitions and resolution.transitions:
        open_by_id = {int(r.id): r for r in open_patient_recalls}
        for trans in resolution.transitions:
            target = open_by_id.get(trans.recall_id)
            if target is None:
                continue
            target.status = trans.new_status
            if trans.cancelled_reason is not None:
                target.cancelled_reason = trans.cancelled_reason
            if trans.new_status == "done" and procedure.encounter_id is not None:
                target.completed_encounter_id = int(procedure.encounter_id)
            target.updated_by_id = user_id
            target.version = int(target.version) + 1

    if replace_existing_for_source:
        for row in existing_for_source:
            if row.status in {"pending", "unreachable"}:
                row.status = "cancelled"
                row.cancelled_reason = superseded_reason
                row.updated_by_id = user_id
        for item in planned:
            await recall_repo.add(
                Recall(
                    public_id=new_ulid(),
                    clinic_id=clinic_id,
                    patient_id=int(procedure.patient_id),
                    source_type="procedure",
                    source_id=int(procedure.id),
                    protocol_id=item.protocol_id,
                    protocol_rule_id=item.protocol_rule_id,
                    reason_key=item.reason_key,
                    due_on=item.due_on,
                    window_days=item.window_days,
                    action_type=item.action_type,
                    action_config=item.action_config,
                    laterality=item.laterality,
                    status="pending",
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
            )
    else:
        # Idempotent backfill / creation on ProcedurePerformed (signing)
        open_source_by_reason = {
            (r.reason_key, r.laterality): r
            for r in existing_for_source
            if r.status in {"pending", "booked", "unreachable"}
        }
        for item in planned:
            existing = open_source_by_reason.get((item.reason_key, item.laterality))
            if existing is not None:
                if existing.protocol_id is None:
                    existing.protocol_id = item.protocol_id
                if existing.protocol_rule_id is None:
                    existing.protocol_rule_id = item.protocol_rule_id
            else:
                await recall_repo.add(
                    Recall(
                        public_id=new_ulid(),
                        clinic_id=clinic_id,
                        patient_id=int(procedure.patient_id),
                        source_type="procedure",
                        source_id=int(procedure.id),
                        protocol_id=item.protocol_id,
                        protocol_rule_id=item.protocol_rule_id,
                        reason_key=item.reason_key,
                        due_on=item.due_on,
                        window_days=item.window_days,
                        action_type=item.action_type,
                        action_config=item.action_config,
                        laterality=item.laterality,
                        status="pending",
                        created_by_id=user_id,
                        updated_by_id=user_id,
                    )
                )

    del devices_repo
    return planned


async def schedule_next_repeating_recall_on_complete(
    session: AsyncSession,
    *,
    completed_recall: Recall,
    completed_on: date,
    user_id: int | None,
) -> Recall | None:
    """When a repeating protocol recall is marked done, schedule the next occurrence unless stopped."""

    if completed_recall.protocol_rule_id is None:
        return None
    proto_repo = ProtocolRepository(session, clinic_id=int(completed_recall.clinic_id))
    rule = await proto_repo.get_rule_by_id(int(completed_recall.protocol_rule_id))
    if rule is None:
        return None
    protocol = await proto_repo.get_protocol_by_id(int(rule.protocol_id))
    if protocol is None or not protocol.is_active:
        return None

    rule_spec = ProtocolRuleSpec(
        protocol_id=int(protocol.id),
        protocol_code=protocol.code,
        rule_id=int(rule.id),
        sequence=int(rule.sequence),
        offset_days=int(rule.offset_days),
        window_days=int(rule.window_days),
        action_type=rule.action_type,
        action_config=(
            dict(rule.action_config) if rule.action_config is not None else None
        ),
        condition=dict(rule.condition) if rule.condition is not None else None,
        label_key=rule.label_key,
    )
    config = rule_spec.action_config or {}
    repeat_months = config.get("repeatEveryMonths")
    repeat_days = config.get("repeatEveryDays")
    if not (
        (isinstance(repeat_months, int) and repeat_months > 0)
        or (isinstance(repeat_days, int) and repeat_days > 0)
    ):
        return None

    patient_devices = (
        (
            await session.execute(
                select(EarDevice).where(
                    EarDevice.clinic_id == int(completed_recall.clinic_id),
                    EarDevice.patient_id == int(completed_recall.patient_id),
                    EarDevice.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    device_specs = tuple(
        DeviceStateSpec(
            device_type=row.device_type,
            laterality=row.laterality,
            status=row.status,
        )
        for row in patient_devices
    )
    laterality = completed_recall.laterality or "na"
    if is_stop_condition_met(
        rule_spec.action_config,
        laterality=laterality,
        devices=device_specs,
        attributes={},
    ):
        return None

    open_recalls = await ProcedureRecallRepository(
        session, clinic_id=int(completed_recall.clinic_id)
    ).list_open_for_patient(int(completed_recall.patient_id))
    if any(
        int(r.id) != int(completed_recall.id)
        and r.reason_key == rule.label_key
        and r.laterality == completed_recall.laterality
        for r in open_recalls
    ):
        return None

    res = resolve_protocol(
        rules=(
            ProtocolRuleSpec(
                protocol_id=rule_spec.protocol_id,
                protocol_code=rule_spec.protocol_code,
                rule_id=rule_spec.rule_id,
                sequence=rule_spec.sequence,
                offset_days=rule_spec.offset_days,
                window_days=rule_spec.window_days,
                action_type=rule_spec.action_type,
                action_config=rule_spec.action_config,
                condition=None,
                label_key=rule_spec.label_key,
            ),
        ),
        context=ProcedureTriggerContext(
            procedure_concept_code=protocol.code,
            performed_on=completed_on,
            laterality=laterality,
            attributes={},
            devices=device_specs,
        ),
    )
    if not res.planned:
        return None
    item = res.planned[0]
    next_row = Recall(
        public_id=new_ulid(),
        clinic_id=int(completed_recall.clinic_id),
        patient_id=int(completed_recall.patient_id),
        source_type=completed_recall.source_type,
        source_id=completed_recall.source_id,
        protocol_id=item.protocol_id,
        protocol_rule_id=item.protocol_rule_id,
        reason_key=item.reason_key,
        due_on=item.due_on,
        window_days=item.window_days,
        action_type=item.action_type,
        action_config=item.action_config,
        laterality=item.laterality,
        status="pending",
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    await ProcedureRecallRepository(
        session, clinic_id=int(completed_recall.clinic_id)
    ).add(next_row)
    return next_row


async def handle_procedure_performed(event: DomainEvent) -> None:
    """Domain event listener for ``procedure.performed`` (P3-08)."""

    clinic_id_raw = event.payload.get("clinic_id")
    procedure_public_id = event.payload.get("procedure_public_id")
    concept_code = event.payload.get("procedure_concept_code")
    if not isinstance(clinic_id_raw, int) or not isinstance(procedure_public_id, str):
        return
    factory = get_session_factory()
    async with factory() as session:
        clinic = await ClinicRepository(session).get(clinic_id_raw)
        if clinic is None:
            return
        procedure = await ProcedureRecordRepository(
            session, clinic_id=clinic_id_raw
        ).get_detail(procedure_public_id)
        if procedure is None:
            return
        office = await OfficeProcedureRepository(
            session, clinic_id=clinic_id_raw
        ).get_for_procedure(int(procedure.id))
        performed_on = clinic_local_date(procedure.performed_at, clinic.timezone)
        code = (
            str(concept_code)
            if isinstance(concept_code, str)
            else procedure.procedure_concept.code
        )
        await resolve_and_sync_procedure_recalls(
            session,
            clinic_id=clinic_id_raw,
            user_id=procedure.signed_by_id or procedure.updated_by_id,
            procedure=procedure,
            procedure_concept_code=code,
            performed_on=performed_on,
            office=office,
            replace_existing_for_source=False,
            apply_completion_transitions=True,
        )
        await session.commit()
