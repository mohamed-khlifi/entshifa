"""Seed system recall protocols mapped from Feature Spec Appendix C (P3-08).

All intervals live in the ``protocol`` and ``protocol_rule`` tables so clinics
can edit them without a code change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.features.recalls.models import Protocol, ProtocolRule
from ent.features.terminology.models import Concept


@dataclass(frozen=True, slots=True)
class ProtocolRuleSeedSpec:
    sequence: int
    offset_days: int
    window_days: int
    action_type: str
    label_key: str
    action_config: dict[str, Any] | None = None
    condition: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ProtocolSeedSpec:
    code: str
    name_key: str
    trigger_type: str
    trigger_concept_codes: tuple[str, ...]
    rules: tuple[ProtocolRuleSeedSpec, ...]


SYSTEM_PROTOCOLS: tuple[ProtocolSeedSpec, ...] = (
    # Appendix C: Epistaxis pack removal 48-72 h (2 days + 1 day window).
    ProtocolSeedSpec(
        code="PROT.EPISTAXIS_PACK",
        name_key="recalls.protocols.epistaxis_pack",
        trigger_type="procedure",
        trigger_concept_codes=("PROC.EPISTAXIS_MANAGEMENT",),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=2,
                window_days=1,
                action_type="visit",
                label_key="office_pack_removal",
                condition={
                    "field": "method",
                    "in": ["anterior_pack", "posterior_pack", "balloon"],
                },
                action_config={
                    "dueDateField": "removal_due_date",
                    "completedByProcedureCodes": [
                        "PROC.NASAL_ENDOSCOPY",
                        "PROC.EPISTAXIS_MANAGEMENT",
                    ],
                },
            ),
        ),
    ),
    # Appendix C: Otitis externa wick removal/replace 48-72 h (3 days + 1 day window).
    ProtocolSeedSpec(
        code="PROT.EAR_WICK",
        name_key="recalls.protocols.ear_wick",
        trigger_type="procedure",
        trigger_concept_codes=("PROC.EAR_WICK",),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=3,
                window_days=1,
                action_type="visit",
                label_key="otology_wick_removal",
                action_config={
                    "dueDateField": "removal_due_date",
                    "completedByProcedureCodes": [
                        "PROC.OTOSCOPY",
                        "PROC.OTOMICROSCOPY",
                        "PROC.EAR_WICK",
                    ],
                },
            ),
        ),
    ),
    # Ticket P3-08 & Appendix C: Splints 5-7 days (offset 5 days, window 3 days -> up to day 8/10).
    ProtocolSeedSpec(
        code="PROT.NASAL_SPLINT",
        name_key="recalls.protocols.nasal_splint",
        trigger_type="procedure",
        trigger_concept_codes=("PROC.NASAL_FRACTURE_REDUCTION",),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=5,
                window_days=3,
                action_type="visit",
                label_key="office_splint_removal",
                action_config={
                    "dueDateField": "removal_due_date",
                    "completedByProcedureCodes": [
                        "PROC.NASAL_ENDOSCOPY",
                        "PROC.NASAL_FRACTURE_REDUCTION",
                    ],
                },
            ),
        ),
    ),
    # Appendix C & add-recall-protocol skill:
    # Ventilation tubes: visit 3-4 weeks (21d + 7d window); audiogram at 3 months (90d + 14d window)
    # if hearing loss pre-op; then every 6 months (180d + 30d window) until extrusion/removal.
    ProtocolSeedSpec(
        code="PROT.VENTILATION_TUBE",
        name_key="recalls.protocols.ventilation_tube",
        trigger_type="procedure",
        trigger_concept_codes=("PROC.VENTILATION_TUBE",),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=21,
                window_days=7,
                action_type="visit",
                label_key="otology_tube_patency",
                action_config={
                    "completedByProcedureCodes": [
                        "PROC.OTOSCOPY",
                        "PROC.OTOMICROSCOPY",
                    ],
                    "cancelledByProcedureCodes": ["PROC.TUBE_REMOVAL"],
                },
            ),
            ProtocolRuleSeedSpec(
                sequence=2,
                offset_days=90,
                window_days=14,
                action_type="test",
                label_key="otology_tube_audiogram",
                condition={"field": "has_preop_hearing_loss", "eq": True},
                action_config={
                    "test": "audiogram",
                    "cancelledByProcedureCodes": ["PROC.TUBE_REMOVAL"],
                },
            ),
            ProtocolRuleSeedSpec(
                sequence=3,
                offset_days=180,
                window_days=30,
                action_type="visit",
                label_key="otology_tube_check",
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
            ),
        ),
    ),
    # Appendix C: Mastoid cavity cleaning every 6-12 months (180d + 30d window, repeating).
    ProtocolSeedSpec(
        code="PROT.CAVITY_CLEANING",
        name_key="recalls.protocols.cavity_cleaning",
        trigger_type="procedure",
        trigger_concept_codes=("PROC.CAVITY_CLEANING",),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=180,
                window_days=30,
                action_type="visit",
                label_key="otology_cavity_cleaning",
                action_config={
                    "offsetMonths": 6,
                    "repeatEveryMonths": 6,
                    "stopCondition": {
                        "deviceType": "mastoid_cavity",
                        "closedStatuses": ["extruded", "removed"],
                    },
                    "completedByProcedureCodes": [
                        "PROC.CAVITY_CLEANING",
                        "PROC.OTOMICROSCOPY",
                    ],
                },
            ),
        ),
    ),
    # Appendix C: Specimen / histology result review at 7-10 days (7d + 3d window).
    ProtocolSeedSpec(
        code="PROT.SPECIMEN_REVIEW",
        name_key="recalls.protocols.specimen_review",
        trigger_type="procedure",
        trigger_concept_codes=(
            "PROC.FINE_NEEDLE_ASPIRATION",
            "PROC.ORAL_PHARYNGEAL_BIOPSY",
        ),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=7,
                window_days=3,
                action_type="visit",
                label_key="office_specimen_review",
                action_config={
                    "dueDateField": "result_due_date",
                },
            ),
        ),
    ),
    # Appendix C: Sialendoscopy visit at 2-4 weeks (14d + 14d window).
    ProtocolSeedSpec(
        code="PROT.SIALENDOSCOPY_FOLLOWUP",
        name_key="recalls.protocols.sialendoscopy_followup",
        trigger_type="procedure",
        trigger_concept_codes=("PROC.SIALENDOSCOPY",),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=14,
                window_days=14,
                action_type="visit",
                label_key="office_sialendoscopy_review",
                action_config={
                    "dueDateField": "follow_up_date",
                    "completedByProcedureCodes": ["PROC.SIALENDOSCOPY"],
                },
            ),
        ),
    ),
    # Appendix C: Cerumen / foreign-body removal -> recall if canal injury (14d + 7d window).
    ProtocolSeedSpec(
        code="PROT.CANAL_INJURY",
        name_key="recalls.protocols.canal_injury",
        trigger_type="procedure",
        trigger_concept_codes=(
            "PROC.CERUMEN_REMOVAL",
            "PROC.EAR_FOREIGN_BODY",
        ),
        rules=(
            ProtocolRuleSeedSpec(
                sequence=1,
                offset_days=14,
                window_days=7,
                action_type="visit",
                label_key="otology_canal_injury",
                condition={"field": "canal_traumatized", "eq": True},
                action_config={
                    "completedByProcedureCodes": [
                        "PROC.OTOSCOPY",
                        "PROC.OTOMICROSCOPY",
                    ],
                },
            ),
        ),
    ),
)


async def seed_protocols(session: AsyncSession) -> int:
    """Idempotently seed system follow-up protocols and rules."""

    created_count = 0
    concepts = (
        (await session.execute(select(Concept).where(Concept.deleted_at.is_(None))))
        .scalars()
        .all()
    )
    concept_id_by_code = {c.code: int(c.id) for c in concepts}

    for spec in SYSTEM_PROTOCOLS:
        trigger_ids: list[int] = [
            concept_id_by_code[code]
            for code in spec.trigger_concept_codes
            if code in concept_id_by_code
        ]
        existing = (
            await session.execute(
                select(Protocol).where(
                    Protocol.clinic_id.is_(None),
                    Protocol.code == spec.code,
                    Protocol.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            protocol = Protocol(
                public_id=new_ulid(),
                clinic_id=None,
                code=spec.code,
                name_key=spec.name_key,
                trigger_type=spec.trigger_type,
                trigger_concept_ids=trigger_ids,
                is_active=True,
            )
            session.add(protocol)
            await session.flush()
            created_count += 1
        else:
            protocol = existing
            protocol.name_key = spec.name_key
            protocol.trigger_type = spec.trigger_type
            protocol.trigger_concept_ids = trigger_ids
            protocol.is_active = True
            await session.flush()

        existing_rules = (
            (
                await session.execute(
                    select(ProtocolRule).where(
                        ProtocolRule.protocol_id == protocol.id,
                        ProtocolRule.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        rules_by_seq = {int(rule.sequence): rule for rule in existing_rules}

        for rule_spec in spec.rules:
            current = rules_by_seq.get(rule_spec.sequence)
            if current is None:
                session.add(
                    ProtocolRule(
                        public_id=new_ulid(),
                        protocol_id=int(protocol.id),
                        sequence=rule_spec.sequence,
                        offset_days=rule_spec.offset_days,
                        window_days=rule_spec.window_days,
                        action_type=rule_spec.action_type,
                        action_config=rule_spec.action_config,
                        condition=rule_spec.condition,
                        label_key=rule_spec.label_key,
                    )
                )
            else:
                current.offset_days = rule_spec.offset_days
                current.window_days = rule_spec.window_days
                current.action_type = rule_spec.action_type
                current.action_config = rule_spec.action_config
                current.condition = rule_spec.condition
                current.label_key = rule_spec.label_key

    await session.flush()
    return created_count
