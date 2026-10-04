"""Diagnosis and doctor-favourite ORM models (architecture §25.11 / P2-07)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import datetime6, unsigned_bigint
from ent.features.diagnoses.constants import (
    DIAGNOSIS_LATERALITIES,
    DIAGNOSIS_SOURCES,
    DIAGNOSIS_STATUSES,
)
from ent.features.patients.models import PatientProblem
from ent.features.terminology.models import Concept
from ent.features.users.models import User

_LATERALITY_SQL = ",".join(f"'{value}'" for value in DIAGNOSIS_LATERALITIES)
_STATUS_SQL = ",".join(f"'{value}'" for value in DIAGNOSIS_STATUSES)
_SOURCE_SQL = ",".join(f"'{value}'" for value in DIAGNOSIS_SOURCES)


class Diagnosis(ClinicalRecordMixin, Base):
    """A coded diagnosis for one visit. The fact is a concept, never free text."""

    __tablename__ = "diagnosis"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IN ({_LATERALITY_SQL})",
            name="ck_diagnosis__laterality",
        ),
        CheckConstraint(
            f"status IN ({_STATUS_SQL})",
            name="ck_diagnosis__status",
        ),
        CheckConstraint(
            f"source IN ({_SOURCE_SQL})",
            name="ck_diagnosis__source",
        ),
        Index(
            "ix_diagnosis__clinic_id__encounter_id",
            "clinic_id",
            "encounter_id",
        ),
        Index(
            "ix_diagnosis__clinic_id__concept_id__created_at",
            "clinic_id",
            "concept_id",
            "created_at",
        ),
        Index(
            "ix_diagnosis__clinic_id__patient_id__effective_at",
            "clinic_id",
            "patient_id",
            "effective_at",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
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
    laterality: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    certainty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(400), nullable=True)
    promoted_to_problem_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "patient_problem.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_diagnosis__promoted_problem",
        ),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    recorded_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    effective_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    derived_from_diagnosis_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "diagnosis.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_diagnosis__derived_from",
        ),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    concept: Mapped[Concept] = relationship(foreign_keys=[concept_id], lazy="selectin")
    promoted_problem: Mapped[PatientProblem | None] = relationship(
        foreign_keys=[promoted_to_problem_id],
        lazy="selectin",
    )
    recorded_by: Mapped[User | None] = relationship(
        foreign_keys=[recorded_by_id],
        lazy="selectin",
    )
    derived_from: Mapped[Diagnosis | None] = relationship(
        remote_side="Diagnosis.id",
        foreign_keys=[derived_from_diagnosis_id],
        lazy="selectin",
    )
    encounter: Mapped[object] = relationship(
        "Encounter",
        back_populates="diagnoses",
        foreign_keys=[encounter_id],
    )


class UserDiagnosisFavorite(ClinicalRecordMixin, Base):
    """Diagnoses a doctor keeps above search, below complaint-template favourites."""

    __tablename__ = "user_diagnosis_favorite"
    __audit_writes__ = True
    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "user_id",
            "concept_id",
            name="uq_user_dx_favorite__clinic__user__concept",
        ),
        Index(
            "ix_user_dx_favorite__clinic_id__user_id__sort_order",
            "clinic_id",
            "user_id",
            "sort_order",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    concept: Mapped[Concept] = relationship(foreign_keys=[concept_id], lazy="selectin")


from ent.features.encounters.guard import install_diagnosis_guards  # noqa: E402

install_diagnosis_guards(Diagnosis)
