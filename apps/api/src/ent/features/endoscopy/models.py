"""Endoscopy exam ORM model (architecture §25.7 / P3-02).

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
from ent.features.endoscopy.constants import POLYP_SCALES, SCOPE_TYPES
from ent.features.endoscopy.guard import install_endoscopy_guards
from ent.features.observations.models import Observation
from ent.features.procedures.models import ProcedureRecord

_SCOPE_SQL = ",".join(f"'{value}'" for value in SCOPE_TYPES)
_SCALE_SQL = ",".join(f"'{value}'" for value in POLYP_SCALES)


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


class EndoscopyExam(ClinicalRecordMixin, Base):
    """One nasal endoscopy attached to a single procedure record."""

    __tablename__ = "endoscopy_exam"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            f"scope_type IN ({_SCOPE_SQL})",
            name="ck_endoscopy_exam__scope_type",
        ),
        CheckConstraint(
            f"polyp_scale IN ({_SCALE_SQL})",
            name="ck_endoscopy_exam__polyp_scale",
        ),
        CheckConstraint(
            "lund_kennedy_right BETWEEN 0 AND 10",
            name="ck_endoscopy_exam__lk_right",
        ),
        CheckConstraint(
            "lund_kennedy_left BETWEEN 0 AND 10",
            name="ck_endoscopy_exam__lk_left",
        ),
        CheckConstraint(
            "modified_lk_right BETWEEN 0 AND 6",
            name="ck_endoscopy_exam__mod_right",
        ),
        CheckConstraint(
            "modified_lk_left BETWEEN 0 AND 6",
            name="ck_endoscopy_exam__mod_left",
        ),
        CheckConstraint(
            "polyp_grade_right IS NULL OR polyp_grade_right BETWEEN 0 AND 4",
            name="ck_endoscopy_exam__polyp_right",
        ),
        CheckConstraint(
            "polyp_grade_left IS NULL OR polyp_grade_left BETWEEN 0 AND 4",
            name="ck_endoscopy_exam__polyp_left",
        ),
        CheckConstraint(
            "adenoid_obstruction_pct IS NULL OR adenoid_obstruction_pct BETWEEN 0 AND 100",
            name="ck_endoscopy_exam__adenoid",
        ),
        Index(
            "uq_endoscopy_exam__procedure",
            "procedure_record_id",
            unique=True,
        ),
        Index(
            "ix_endoscopy_exam__clinic_procedure",
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
            name="fk_endoscopy_exam__procedure",
        ),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    decongestant_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    lund_kennedy_right: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    lund_kennedy_left: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    modified_lk_right: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    modified_lk_left: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    polyp_grade_right: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    polyp_grade_left: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    polyp_scale: Mapped[str] = mapped_column(String(20), nullable=False)
    adenoid_obstruction_pct: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    conclusion_text: Mapped[str | None] = mapped_column(_medium_text(), nullable=True)

    procedure_record: Mapped[ProcedureRecord] = relationship(
        foreign_keys=[procedure_record_id],
        lazy="selectin",
    )


install_endoscopy_guards(EndoscopyExam, Observation)
