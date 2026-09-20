"""Terminology ORM models (architecture sections 20 and 25.2)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import (
    AuditMixin,
    PublicIdMixin,
    SoftDeleteMixin,
    SurrogatePkMixin,
    TimestampMixin,
    VersionMixin,
)
from ent.core.db.mysql_types import mysql_json, unsigned_bigint

CONCEPT_KINDS = (
    "finding",
    "anatomy",
    "diagnosis",
    "procedure",
    "qualifier",
    "laterality",
    "unit",
    "instrument_item",
    "drug",
    "allergy",
)

RELATIONSHIP_TYPES = (
    "is_a",
    "part_of",
    "maps_to",
    "site_of",
    "default_normal_for",
)


class _ReferenceMixins(
    SurrogatePkMixin,
    PublicIdMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    VersionMixin,
):
    """Shared columns for terminology reference tables."""


class CodeSystem(
    SurrogatePkMixin,
    PublicIdMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    Base,
):
    """Global coding system. ``version`` is the release label (not optimistic lock)."""

    __tablename__ = "code_system"

    code: Mapped[str] = mapped_column(
        String(40, collation="utf8mb4_0900_as_cs"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    uri: Mapped[str | None] = mapped_column(String(255), nullable=True)

    concepts: Mapped[list[Concept]] = relationship(back_populates="code_system")


class Concept(_ReferenceMixins, Base):
    __tablename__ = "concept"
    __table_args__ = (
        UniqueConstraint("code_system_id", "code", name="uq_concept__code_system_id__code"),
        CheckConstraint(
            "kind IN ("
            + ",".join(f"'{k}'" for k in CONCEPT_KINDS)
            + ")",
            name="ck_concept__kind",
        ),
        Index("ix_concept__kind__parent_id", "kind", "parent_id"),
        Index("ix_concept__clinic_id__kind", "clinic_id", "kind"),
    )

    code_system_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("code_system.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    properties: Mapped[dict[str, Any] | None] = mapped_column(mysql_json(), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        index=True,
    )

    code_system: Mapped[CodeSystem] = relationship(back_populates="concepts")
    translations: Mapped[list[ConceptTranslation]] = relationship(back_populates="concept")


class ConceptTranslation(_ReferenceMixins, Base):
    __tablename__ = "concept_translation"
    __table_args__ = (
        UniqueConstraint(
            "concept_id",
            "locale",
            "clinic_scope",
            name="uq_concept_translation__concept_id__locale__clinic_scope",
        ),
        Index("ix_concept_translation__locale", "locale"),
    )

    concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    display: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(400), nullable=True)
    abbreviation: Mapped[str | None] = mapped_column(String(40), nullable=True)
    patient_friendly: Mapped[str | None] = mapped_column(String(400), nullable=True)
    synonyms: Mapped[list[Any] | None] = mapped_column(mysql_json(), nullable=True)
    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    # MySQL UNIQUE treats NULLs as distinct; scope 0 = global translation.
    clinic_scope: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("IFNULL(clinic_id, 0)", persisted=True),
    )

    concept: Mapped[Concept] = relationship(back_populates="translations")


class ConceptRelationship(SurrogatePkMixin, PublicIdMixin, Base):
    __tablename__ = "concept_relationship"
    __table_args__ = (
        UniqueConstraint(
            "source_concept_id",
            "target_concept_id",
            "type",
            name="uq_concept_relationship__source__target__type",
        ),
        CheckConstraint(
            "type IN (" + ",".join(f"'{t}'" for t in RELATIONSHIP_TYPES) + ")",
            name="ck_concept_relationship__type",
        ),
        Index("ix_concept_relationship__target_concept_id", "target_concept_id"),
    )

    source_concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    target_concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)


class ValueSet(_ReferenceMixins, Base):
    __tablename__ = "value_set"

    code: Mapped[str] = mapped_column(
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
        unique=True,
    )
    name_key: Mapped[str] = mapped_column(String(80), nullable=False)
    description_key: Mapped[str | None] = mapped_column(String(120), nullable=True)

    members: Mapped[list[ValueSetMember]] = relationship(back_populates="value_set")


class ValueSetMember(SurrogatePkMixin, PublicIdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "value_set_member"
    __table_args__ = (
        UniqueConstraint(
            "value_set_id",
            "concept_id",
            "clinic_scope",
            name="uq_value_set_member__value_set_id__concept_id__clinic_scope",
        ),
        Index("ix_value_set_member__value_set_id__sort_order", "value_set_id", "sort_order"),
    )

    value_set_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("value_set.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    concept_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("concept.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    clinic_scope: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("IFNULL(clinic_id, 0)", persisted=True),
    )

    value_set: Mapped[ValueSet] = relationship(back_populates="members")
    concept: Mapped[Concept] = relationship()
