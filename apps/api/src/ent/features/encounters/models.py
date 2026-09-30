"""Encounter ORM models (architecture §25.5 / P2-02)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin, GlobalRecordMixin
from ent.core.db.mysql_types import datetime6, mysql_json, unsigned_bigint, varbinary
from ent.core.db.types import LateralityType
from ent.features.clinics.models import Site
from ent.features.encounters.constants import ENCOUNTER_STATUSES, ENCOUNTER_TYPES
from ent.features.patients.models import Patient
from ent.features.scheduling.models import Appointment
from ent.features.terminology.models import Concept
from ent.features.users.models import User

_LATERALITY_SQL = "'right','left','bilateral','midline','na'"


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


def _sql_in(column: str, values: tuple[str, ...]) -> str:
    inner = ",".join(f"'{value}'" for value in values)
    return f"{column} IN ({inner})"


class EncounterTemplate(GlobalRecordMixin, Base):
    """Visit shape selected by complaint. NULL clinic_id is a system template.

    Doctor-owned rows set user_id. Clinic-wide rows leave user_id NULL.
    Seeding and routing belong to P2-03. System rows are not auto-audited:
    the audit writer requires a clinic, and a system template has none.
    """

    __tablename__ = "encounter_template"
    __table_args__ = (
        Index(
            "uq_encounter_template__scope__code",
            "scope_clinic_id",
            "scope_user_id",
            "code",
            unique=True,
        ),
        Index("ix_encounter_template__code", "code"),
    )

    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    scope_clinic_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(clinic_id, 0)", persisted=True),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    scope_user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(user_id, 0)", persisted=True),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    name_key: Mapped[str] = mapped_column(String(80), nullable=False)
    trigger_concept_ids: Mapped[list[Any]] = mapped_column(mysql_json(), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )


class Encounter(ClinicalRecordMixin, Base):
    """One visit. Signed rows are immutable; corrections are addenda."""

    __tablename__ = "encounter"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _sql_in("encounter_type", ENCOUNTER_TYPES),
            name="ck_encounter__encounter_type",
        ),
        CheckConstraint(
            _sql_in("status", ENCOUNTER_STATUSES),
            name="ck_encounter__status",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_encounter__time_range",
        ),
        Index(
            "ix_encounter__clinic_patient_started",
            "clinic_id",
            "patient_id",
            text("started_at DESC"),
        ),
        Index(
            "ix_encounter__clinic_user_status",
            "clinic_id",
            "user_id",
            "status",
        ),
    )

    site_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("site.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    appointment_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("appointment.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    encounter_type: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    template_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter_template.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    chief_complaint_summary: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    history_text: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)
    assessment_text: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)
    plan_text: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    signed_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    signed_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    locked_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )

    patient: Mapped[Patient] = relationship(
        foreign_keys=[patient_id],
        lazy="selectin",
    )
    site: Mapped[Site] = relationship(foreign_keys=[site_id], lazy="selectin")
    clinician: Mapped[User] = relationship(
        foreign_keys=[user_id],
        lazy="selectin",
        overlaps="signed_by",
    )
    signed_by: Mapped[User | None] = relationship(
        foreign_keys=[signed_by_id],
        lazy="selectin",
        overlaps="clinician",
    )
    appointment: Mapped[Appointment | None] = relationship(
        foreign_keys=[appointment_id],
        lazy="selectin",
    )
    template: Mapped[EncounterTemplate | None] = relationship(
        foreign_keys=[template_id],
        lazy="selectin",
    )
    previous_encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[previous_encounter_id],
        remote_side="Encounter.id",
        lazy="selectin",
    )
    complaints: Mapped[list[EncounterComplaint]] = relationship(
        back_populates="encounter",
        order_by="EncounterComplaint.sort_order",
        lazy="selectin",
    )
    addenda: Mapped[list[EncounterAddendum]] = relationship(
        back_populates="encounter",
        order_by="EncounterAddendum.created_at",
        lazy="selectin",
    )
    signatures: Mapped[list[EncounterSignature]] = relationship(
        back_populates="encounter",
        order_by="EncounterSignature.signed_at",
        lazy="selectin",
    )


class EncounterComplaint(ClinicalRecordMixin, Base):
    """A coded reason for the visit. Free text stays on the encounter."""

    __tablename__ = "encounter_complaint"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY_SQL})",
            name="ck_encounter_complaint__laterality",
        ),
        Index(
            "ix_encounter_complaint__clinic_encounter",
            "clinic_id",
            "encounter_id",
        ),
    )

    encounter_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    laterality: Mapped[str | None] = mapped_column(LateralityType(), nullable=True)
    duration_text: Mapped[str | None] = mapped_column(String(60), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    encounter: Mapped[Encounter] = relationship(back_populates="complaints")
    concept: Mapped[Concept] = relationship(foreign_keys=[concept_id], lazy="selectin")


class EncounterAddendum(ClinicalRecordMixin, Base):
    """The only legal correction of a signed encounter."""

    __tablename__ = "encounter_addendum"
    __audit_writes__ = True
    __table_args__ = (
        Index(
            "ix_encounter_addendum__clinic_encounter_created",
            "clinic_id",
            "encounter_id",
            text("created_at DESC"),
        ),
    )

    encounter_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    author_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(_medium_text(), nullable=False)

    encounter: Mapped[Encounter] = relationship(back_populates="addenda")
    author: Mapped[User] = relationship(foreign_keys=[author_id], lazy="selectin")


class EncounterSignature(ClinicalRecordMixin, Base):
    """Who signed, when, from where, and which content hash they signed."""

    __tablename__ = "encounter_signature"
    __audit_writes__ = True
    __table_args__ = (
        Index(
            "ix_encounter_signature__clinic_encounter",
            "clinic_id",
            "encounter_id",
        ),
    )

    encounter_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("encounter.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    ip_address: Mapped[bytes | None] = mapped_column(varbinary(16), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    encounter: Mapped[Encounter] = relationship(back_populates="signatures")
    signer: Mapped[User] = relationship(foreign_keys=[user_id], lazy="selectin")


from ent.features.encounters.guard import install_encounter_guards  # noqa: E402

install_encounter_guards(
    Encounter,
    EncounterComplaint,
    EncounterAddendum,
    EncounterSignature,
)
