"""Procedure record ORM models (architecture §25.7 / P3-01).

``procedure_record`` is the parent of every ENT procedure. Child exams in later
tickets hold a ``procedure_record_id`` and do not repeat these columns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint, varbinary
from ent.core.db.types import LateralityType
from ent.features.encounters.models import Encounter
from ent.features.patients.models import Patient
from ent.features.procedures.constants import (
    ANESTHESIA_TYPES,
    PROCEDURE_SETTINGS,
    PROCEDURE_STATUSES,
    TOLERANCE_VALUES,
)
from ent.features.terminology.models import Concept
from ent.features.users.models import User

_STATUS_SQL = ",".join(f"'{value}'" for value in PROCEDURE_STATUSES)
_SETTING_SQL = ",".join(f"'{value}'" for value in PROCEDURE_SETTINGS)
_ANESTHESIA_SQL = ",".join(f"'{value}'" for value in ANESTHESIA_TYPES)
_TOLERANCE_SQL = ",".join(f"'{value}'" for value in TOLERANCE_VALUES)
_LATERALITY_SQL = "'right','left','bilateral','midline','na'"


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


class ProcedureRecord(ClinicalRecordMixin, Base):
    """One performed procedure. Signing freezes the row; corrections are addenda."""

    __tablename__ = "procedure_record"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_SQL})",
            name="ck_procedure_record__status",
        ),
        CheckConstraint(
            f"setting IN ({_SETTING_SQL})",
            name="ck_procedure_record__setting",
        ),
        CheckConstraint(
            f"anesthesia IN ({_ANESTHESIA_SQL})",
            name="ck_procedure_record__anesthesia",
        ),
        CheckConstraint(
            f"laterality IN ({_LATERALITY_SQL})",
            name="ck_procedure_record__laterality",
        ),
        CheckConstraint(
            f"tolerance IS NULL OR tolerance IN ({_TOLERANCE_SQL})",
            name="ck_procedure_record__tolerance",
        ),
        Index(
            "ix_procedure_record__clinic_id__patient_id__performed_at",
            "clinic_id",
            "patient_id",
            text("performed_at DESC"),
        ),
        Index(
            "ix_procedure_record__clinic_id__procedure_concept_id",
            "clinic_id",
            "procedure_concept_id",
        ),
        Index(
            "ix_procedure_record__clinic_id__encounter_id",
            "clinic_id",
            "encounter_id",
        ),
        Index(
            "ix_procedure_record__clinic_id__status",
            "clinic_id",
            "status",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "patient.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record__patient",
        ),
        nullable=False,
    )
    encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record__encounter",
        ),
        nullable=True,
    )
    procedure_concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record__procedure_concept",
        ),
        nullable=False,
    )
    performed_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record__performed_by",
        ),
        nullable=False,
    )
    laterality: Mapped[str] = mapped_column(
        LateralityType(),
        nullable=False,
        default="na",
        server_default="na",
    )
    anesthesia: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="none",
        server_default="none",
    )
    setting: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="office",
        server_default="office",
    )
    instrument: Mapped[str | None] = mapped_column(String(100), nullable=True)
    indication_text: Mapped[str | None] = mapped_column(String(400), nullable=True)
    tolerance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    complication_concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record__complication_concept",
        ),
        nullable=True,
    )
    complication_note: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    signed_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    signed_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record__signed_by",
        ),
        nullable=True,
    )
    signed_role: Mapped[str | None] = mapped_column(String(30), nullable=True)
    signed_ip: Mapped[bytes | None] = mapped_column(varbinary(16), nullable=True)
    locked_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    patient: Mapped[Patient] = relationship(
        foreign_keys=[patient_id],
        lazy="raise",
    )
    encounter: Mapped[Encounter | None] = relationship(
        foreign_keys=[encounter_id],
        lazy="raise",
    )
    procedure_concept: Mapped[Concept] = relationship(
        foreign_keys=[procedure_concept_id],
        lazy="raise",
        overlaps="complication_concept",
    )
    complication_concept: Mapped[Concept | None] = relationship(
        foreign_keys=[complication_concept_id],
        lazy="raise",
        overlaps="procedure_concept",
    )
    performed_by: Mapped[User] = relationship(
        foreign_keys=[performed_by_id],
        lazy="raise",
        overlaps="signed_by",
    )
    signed_by: Mapped[User | None] = relationship(
        foreign_keys=[signed_by_id],
        lazy="raise",
        overlaps="performed_by",
    )
    addenda: Mapped[list[ProcedureRecordAddendum]] = relationship(
        back_populates="procedure_record",
        lazy="raise",
        order_by="ProcedureRecordAddendum.created_at",
    )


class ProcedureRecordAddendum(ClinicalRecordMixin, Base):
    """The only legal correction of a signed procedure."""

    __tablename__ = "procedure_record_addendum"
    __audit_writes__ = True
    __table_args__ = (
        Index(
            "ix_proc_addendum__clinic_proc_created",
            "clinic_id",
            "procedure_record_id",
            text("created_at DESC"),
        ),
    )

    procedure_record_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "procedure_record.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record_addendum__procedure_record",
        ),
        nullable=False,
    )
    author_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_procedure_record_addendum__author",
        ),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(_medium_text(), nullable=False)

    procedure_record: Mapped[ProcedureRecord] = relationship(back_populates="addenda")
    author: Mapped[User] = relationship(foreign_keys=[author_id], lazy="raise")


from ent.features.procedures.guard import install_procedure_guards  # noqa: E402

install_procedure_guards(ProcedureRecord, ProcedureRecordAddendum)
