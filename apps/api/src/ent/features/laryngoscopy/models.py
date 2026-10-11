"""Laryngoscopy exam ORM model (architecture §25.7 / P3-04).

Scores on this row are a snapshot of the engines. The observations are the
source the engines recompute from. Signing the parent procedure freezes both.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.mysql_types import unsigned_bigint
from ent.features.laryngoscopy.constants import (
    AMPLITUDE_VALUES,
    GLOTTIC_CLOSURE_VALUES,
    MOBILITY_VALUES,
    MUCOSAL_WAVE_VALUES,
    NON_VIBRATING_VALUES,
    PERIODICITY_VALUES,
    PHASE_CLOSURE_VALUES,
    PHASE_SYMMETRY_VALUES,
    POSITION_VALUES,
    SCOPE_TYPES,
    SUPRAGLOTTIC_VALUES,
    SYMMETRY_VALUES,
    VERTICAL_LEVEL_VALUES,
)
from ent.features.laryngoscopy.guard import install_laryngoscopy_guards
from ent.features.procedures.models import ProcedureRecord


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


def _in(column: str, values: tuple[str, ...], *, nullable: bool) -> str:
    rendered = ",".join(f"'{value}'" for value in values)
    clause = f"{column} IN ({rendered})"
    if nullable:
        return f"{column} IS NULL OR {clause}"
    return clause


class LaryngoscopyExam(ClinicalRecordMixin, Base):
    """One fiberoptic laryngoscopy attached to a single procedure record."""

    __tablename__ = "laryngoscopy_exam"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in("scope_type", SCOPE_TYPES, nullable=False),
            name="ck_laryngoscopy_exam__scope_type",
        ),
        CheckConstraint(
            _in("vf_mobility_right", MOBILITY_VALUES, nullable=False),
            name="ck_laryngoscopy_exam__vf_mob_r",
        ),
        CheckConstraint(
            _in("vf_mobility_left", MOBILITY_VALUES, nullable=False),
            name="ck_laryngoscopy_exam__vf_mob_l",
        ),
        CheckConstraint(
            _in("vf_position_right", POSITION_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__vf_pos_r",
        ),
        CheckConstraint(
            _in("vf_position_left", POSITION_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__vf_pos_l",
        ),
        CheckConstraint(
            _in("glottic_closure", GLOTTIC_CLOSURE_VALUES, nullable=False),
            name="ck_laryngoscopy_exam__glottic",
        ),
        CheckConstraint(
            _in("supraglottic_pattern", SUPRAGLOTTIC_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__supraglottic",
        ),
        CheckConstraint(
            _in("symmetry", SYMMETRY_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__symmetry",
        ),
        CheckConstraint(
            _in("periodicity", PERIODICITY_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__periodicity",
        ),
        CheckConstraint(
            _in("amplitude_right", AMPLITUDE_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__amp_r",
        ),
        CheckConstraint(
            _in("amplitude_left", AMPLITUDE_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__amp_l",
        ),
        CheckConstraint(
            _in("mucosal_wave_right", MUCOSAL_WAVE_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__wave_r",
        ),
        CheckConstraint(
            _in("mucosal_wave_left", MUCOSAL_WAVE_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__wave_l",
        ),
        CheckConstraint(
            _in("phase_closure", PHASE_CLOSURE_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__phase_close",
        ),
        CheckConstraint(
            _in("phase_symmetry", PHASE_SYMMETRY_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__phase_sym",
        ),
        CheckConstraint(
            _in("vertical_level", VERTICAL_LEVEL_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__vertical",
        ),
        CheckConstraint(
            _in("non_vibrating_segment", NON_VIBRATING_VALUES, nullable=True),
            name="ck_laryngoscopy_exam__non_vib",
        ),
        CheckConstraint(
            "rfs_score IS NULL OR rfs_score BETWEEN 0 AND 26",
            name="ck_laryngoscopy_exam__rfs",
        ),
        CheckConstraint(
            "grbas_g IS NULL OR grbas_g BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_g",
        ),
        CheckConstraint(
            "grbas_r IS NULL OR grbas_r BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_r",
        ),
        CheckConstraint(
            "grbas_b IS NULL OR grbas_b BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_b",
        ),
        CheckConstraint(
            "grbas_a IS NULL OR grbas_a BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_a",
        ),
        CheckConstraint(
            "grbas_s IS NULL OR grbas_s BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_s",
        ),
        CheckConstraint(
            "pas_score IS NULL OR pas_score BETWEEN 1 AND 8",
            name="ck_laryngoscopy_exam__pas",
        ),
        Index("uq_laryngoscopy_exam__procedure", "procedure_record_id", unique=True),
        Index(
            "ix_laryngoscopy_exam__clinic_procedure",
            "clinic_id",
            "procedure_record_id",
        ),
    )

    procedure_record_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "procedure_record.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
            name="fk_laryngoscopy_exam__procedure",
        ),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False)
    vf_mobility_right: Mapped[str] = mapped_column(String(20), nullable=False)
    vf_mobility_left: Mapped[str] = mapped_column(String(20), nullable=False)
    vf_position_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vf_position_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    glottic_closure: Mapped[str] = mapped_column(String(20), nullable=False)
    supraglottic_pattern: Mapped[str | None] = mapped_column(String(20), nullable=True)
    stroboscopy_performed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    symmetry: Mapped[str | None] = mapped_column(String(20), nullable=True)
    periodicity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amplitude_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amplitude_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mucosal_wave_right: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mucosal_wave_left: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phase_closure: Mapped[str | None] = mapped_column(String(30), nullable=True)
    phase_symmetry: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vertical_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    non_vibrating_segment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fees_performed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    rfs_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    grbas_g: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    grbas_r: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    grbas_b: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    grbas_a: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    grbas_s: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    pas_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    conclusion_text: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)

    procedure_record: Mapped[ProcedureRecord] = relationship(
        foreign_keys=[procedure_record_id],
        lazy="selectin",
    )


install_laryngoscopy_guards(LaryngoscopyExam)
