"""Observation ORM models (architecture §25.6 / §26, P2-01)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import datetime6, mysql_json, unsigned_bigint
from ent.core.db.types import LateralityType
from ent.engines.observations.types import (
    OBSERVATION_SOURCES,
    OBSERVATION_STATUSES,
    VALUE_TYPES,
)

_LATERALITY_SQL = "'right','left','bilateral','midline','na'"


def _sql_in(column: str, values: tuple[str, ...]) -> str:
    inner = ",".join(f"'{value}'" for value in values)
    return f"{column} IN ({inner})"


class Observation(ClinicalRecordMixin, Base):
    """One structured finding. The concept is what was observed, not free text."""

    __tablename__ = "observation"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IN ({_LATERALITY_SQL})",
            name="ck_observation__laterality",
        ),
        CheckConstraint(
            _sql_in("status", OBSERVATION_STATUSES),
            name="ck_observation__status",
        ),
        CheckConstraint(
            _sql_in("value_type", VALUE_TYPES),
            name="ck_observation__value_type",
        ),
        CheckConstraint(
            _sql_in("source", OBSERVATION_SOURCES),
            name="ck_observation__source",
        ),
        Index(
            "ix_observation__clinic_patient_concept_effective",
            "clinic_id",
            "patient_id",
            "concept_id",
            text("effective_at DESC"),
        ),
        Index(
            "ix_observation__clinic_encounter_body_site",
            "clinic_id",
            "encounter_id",
            "body_site_concept_id",
        ),
        Index(
            "ix_observation__clinic_encounter_public",
            "clinic_id",
            "encounter_public_id",
        ),
        Index(
            "ix_observation__clinic_concept_value_concept",
            "clinic_id",
            "concept_id",
            "value_concept_id",
        ),
        Index(
            "ix_observation__cohort_ordinal",
            "clinic_id",
            "concept_id",
            "ordinal_value",
            "effective_at",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    # Visit row. Public id remains the stable address used by observations.
    encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__encounter",
        ),
        nullable=True,
    )
    encounter_public_id: Mapped[str | None] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )
    concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__concept",
        ),
        nullable=False,
    )
    body_site_concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__body_site_concept",
        ),
        nullable=True,
    )
    map_region_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    laterality: Mapped[str] = mapped_column(LateralityType(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value_concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__value_concept",
        ),
        nullable=True,
    )
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    value_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean(), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    value_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    value_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ordinal_value: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    qualifiers: Mapped[dict[str, Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )
    effective_at: Mapped[datetime] = mapped_column(datetime6(), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    recorded_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("user.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    confirmed_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__confirmed_by",
        ),
        nullable=True,
    )
    derived_from_observation_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "observation.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__derived_from",
        ),
        nullable=True,
    )
    method_concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation__method_concept",
        ),
        nullable=True,
    )

    components: Mapped[list[ObservationComponent]] = relationship(
        back_populates="observation",
        primaryjoin=(
            "and_(Observation.id == ObservationComponent.observation_id, "
            "ObservationComponent.deleted_at.is_(None))"
        ),
        foreign_keys="ObservationComponent.observation_id",
        lazy="selectin",
    )


class ObservationComponent(ClinicalRecordMixin, Base):
    """One part of a multi-part finding. The parent observation owns the side."""

    __tablename__ = "observation_component"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _sql_in("value_type", VALUE_TYPES),
            name="ck_observation_component__value_type",
        ),
        Index(
            "ix_observation_component__clinic_id__observation_id",
            "clinic_id",
            "observation_id",
        ),
    )

    observation_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("observation.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation_component__concept",
        ),
        nullable=False,
    )
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value_concept_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "concept.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_observation_component__value_concept",
        ),
        nullable=True,
    )
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    value_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean(), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    value_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    value_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ordinal_value: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    qualifiers: Mapped[dict[str, Any] | None] = mapped_column(
        mysql_json(), nullable=True
    )

    observation: Mapped[Observation] = relationship(
        back_populates="components",
        foreign_keys=[observation_id],
    )


class ExaminationSnapshot(ClinicalRecordMixin, Base):
    """Denormalized map state for rendering. Observations remain authoritative."""

    __tablename__ = "examination_snapshot"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"laterality IS NULL OR laterality IN ({_LATERALITY_SQL})",
            name="ck_examination_snapshot__laterality",
        ),
        Index(
            "ix_examination_snapshot__clinic_patient_map_created",
            "clinic_id",
            "patient_id",
            "map_id",
            text("created_at DESC"),
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    encounter_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "encounter.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_examination_snapshot__encounter",
        ),
        nullable=True,
    )
    encounter_public_id: Mapped[str | None] = mapped_column(
        String(26, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )
    map_id: Mapped[str] = mapped_column(String(60), nullable=False)
    laterality: Mapped[str | None] = mapped_column(LateralityType(), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
    rendered_svg_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("attachment.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
