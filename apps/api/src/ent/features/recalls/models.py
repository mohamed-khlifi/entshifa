"""Recall and protocol ORM models (architecture §25.15 / P2-11, P3-08)."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import (
    ClinicalRecordMixin,
    GlobalRecordMixin,
    SurrogatePkMixin,
    TimestampMixin,
)
from ent.core.db.mysql_types import datetime6, mysql_json, unsigned_bigint
from ent.core.db.types import ULIDType
from ent.features.recalls.constants import (
    PROTOCOL_TRIGGER_TYPES,
    RECALL_ACTION_TYPES,
    RECALL_CONTACT_ACTIONS,
    RECALL_LATERALITIES,
    RECALL_OUTCOMES,
    RECALL_SOURCE_TYPES,
    RECALL_STATUSES,
)

if TYPE_CHECKING:
    from ent.features.encounters.models import Encounter
    from ent.features.patients.models import Patient
    from ent.features.scheduling.models import Appointment
    from ent.features.users.models import User

_STATUS_SQL = ",".join(f"'{value}'" for value in RECALL_STATUSES)
_ACTION_SQL = ",".join(f"'{value}'" for value in RECALL_ACTION_TYPES)
_SOURCE_SQL = ",".join(f"'{value}'" for value in RECALL_SOURCE_TYPES)
_LATERALITY_SQL = ",".join(f"'{value}'" for value in RECALL_LATERALITIES)
_CONTACT_SQL = ",".join(f"'{value}'" for value in RECALL_CONTACT_ACTIONS)
_OUTCOME_SQL = ",".join(f"'{value}'" for value in RECALL_OUTCOMES)
_TRIGGER_SQL = ",".join(f"'{value}'" for value in PROTOCOL_TRIGGER_TYPES)


class Protocol(GlobalRecordMixin, Base):
    """Editable follow-up protocol (system default when clinic_id is NULL)."""

    __tablename__ = "protocol"
    __table_args__ = (
        CheckConstraint(
            f"trigger_type IN ({_TRIGGER_SQL})",
            name="ck_protocol__trigger_type",
        ),
        Index(
            "uq_protocol__scope_clinic_id__code",
            "scope_clinic_id",
            "code",
            unique=True,
        ),
        Index("ix_protocol__code", "code"),
        Index("ix_protocol__clinic_id__trigger_type", "clinic_id", "trigger_type"),
    )

    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "clinic.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_protocol__clinic",
        ),
        nullable=True,
    )
    scope_clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(clinic_id, 0)", persisted=True),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    name_key: Mapped[str] = mapped_column(String(80), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_concept_ids: Mapped[list[Any]] = mapped_column(mysql_json(), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    rules: Mapped[list[ProtocolRule]] = relationship(
        "ProtocolRule",
        back_populates="protocol",
        order_by="ProtocolRule.sequence",
        lazy="selectin",
    )


class ProtocolRule(GlobalRecordMixin, Base):
    """One scheduled follow-up step within a protocol."""

    __tablename__ = "protocol_rule"
    __table_args__ = (
        CheckConstraint("sequence >= 1", name="ck_protocol_rule__sequence"),
        CheckConstraint("offset_days >= 0", name="ck_protocol_rule__offset_days"),
        CheckConstraint(
            "window_days >= 0 AND window_days <= 180",
            name="ck_protocol_rule__window_days",
        ),
        CheckConstraint(
            f"action_type IN ({_ACTION_SQL})",
            name="ck_protocol_rule__action_type",
        ),
        Index(
            "uq_protocol_rule__protocol_sequence",
            "protocol_id",
            "sequence",
            unique=True,
        ),
    )

    protocol_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "protocol.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_protocol_rule__protocol",
        ),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    offset_days: Mapped[int] = mapped_column(Integer, nullable=False)
    window_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    action_config: Mapped[dict[str, Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    condition: Mapped[dict[str, Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    label_key: Mapped[str] = mapped_column(String(80), nullable=False)

    protocol: Mapped[Protocol] = relationship(
        "Protocol",
        back_populates="rules",
        lazy="raise",
    )


class Recall(ClinicalRecordMixin, Base):
    """A structured follow-up. Manual rows are created from the visit plan."""

    __tablename__ = "recall"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_SQL})",
            name="ck_recall__status",
        ),
        CheckConstraint(
            f"action_type IN ({_ACTION_SQL})",
            name="ck_recall__action_type",
        ),
        CheckConstraint(
            f"source_type IN ({_SOURCE_SQL})",
            name="ck_recall__source_type",
        ),
        CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY_SQL})",
            name="ck_recall__laterality",
        ),
        CheckConstraint(
            "window_days >= 0 AND window_days <= 180",
            name="ck_recall__window_days",
        ),
        CheckConstraint("attempts >= 0", name="ck_recall__attempts"),
        Index("ix_recall__clinic_id__status__due_on", "clinic_id", "status", "due_on"),
        Index(
            "ix_recall__clinic_id__patient_id__status",
            "clinic_id",
            "patient_id",
            "status",
        ),
        Index(
            "ix_recall__clinic_id__patient_id__due_on",
            "clinic_id",
            "patient_id",
            "due_on",
        ),
        Index(
            "ix_recall__clinic_id__protocol_rule_id",
            "clinic_id",
            "protocol_rule_id",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "patient.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall__patient",
        ),
        nullable=False,
    )
    protocol_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "protocol.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall__protocol",
        ),
        nullable=True,
    )
    protocol_rule_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "protocol_rule.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall__protocol_rule",
        ),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    reason_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reason_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason_locale: Mapped[str | None] = mapped_column(String(10), nullable=True)
    due_on: Mapped[date] = mapped_column(Date, nullable=False)
    window_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=14, server_default="14"
    )
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    action_config: Mapped[dict[str, Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    laterality: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    appointment_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "appointment.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall__appointment",
        ),
        nullable=True,
    )
    completed_encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall__completed_encounter",
        ),
        nullable=True,
    )
    attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    cancelled_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall__assigned_to",
        ),
        nullable=True,
    )

    patient: Mapped[Patient] = relationship(
        "Patient",
        foreign_keys=[patient_id],
        lazy="raise",
    )
    appointment: Mapped[Appointment | None] = relationship(
        "Appointment",
        foreign_keys=[appointment_id],
        lazy="raise",
    )
    completed_encounter: Mapped[Encounter | None] = relationship(
        "Encounter",
        foreign_keys=[completed_encounter_id],
        lazy="raise",
    )
    assigned_to: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        lazy="raise",
    )


class RecallAction(ClinicalRecordMixin, Base):
    """One contact or booking attempt against a recall."""

    __tablename__ = "recall_action"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"action IN ({_CONTACT_SQL})",
            name="ck_recall_action__action",
        ),
        CheckConstraint(
            f"outcome IS NULL OR outcome IN ({_OUTCOME_SQL})",
            name="ck_recall_action__outcome",
        ),
        Index(
            "ix_recall_action__clinic_id__recall_id__performed_at",
            "clinic_id",
            "recall_id",
            "performed_at",
        ),
    )

    recall_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "recall.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall_action__recall",
        ),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_recall_action__performed_by",
        ),
        nullable=False,
    )
    outcome: Mapped[str | None] = mapped_column(String(40), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note_locale: Mapped[str | None] = mapped_column(String(10), nullable=True)

    recall: Mapped[Recall] = relationship(foreign_keys=[recall_id], lazy="raise")


class RecallRequestIdempotency(SurrogatePkMixin, TimestampMixin, Base):
    """Idempotency-Key memory for recall creates."""

    __tablename__ = "recall_request_idempotency"
    __table_args__ = (
        Index(
            "uq_recall_idempotency__clinic_id__idempotency_key",
            "clinic_id",
            "idempotency_key",
            unique=True,
        ),
    )

    public_id: Mapped[str] = mapped_column(ULIDType(), nullable=False, unique=True)
    clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(80, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    request_hash: Mapped[str] = mapped_column(
        String(64, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    resource_public_id: Mapped[str] = mapped_column(ULIDType(), nullable=False)
