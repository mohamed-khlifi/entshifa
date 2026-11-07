"""Questionnaire instrument ORM models (architecture §25.10 / P5-01)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ent.core.db.base import Base
from ent.core.db.mixins import (
    AuditMixin,
    GlobalRecordMixin,
    PublicIdMixin,
    SoftDeleteMixin,
    SurrogatePkMixin,
    TimestampMixin,
)
from ent.core.db.mysql_types import mysql_json, unsigned_bigint
from ent.features.questionnaires.constants import (
    INSTRUMENT_CATEGORIES,
    INSTRUMENT_LOCALES,
    INSTRUMENT_RESPONDENTS,
    INSTRUMENT_SCORING_TYPES,
)


def _in_check(column: str, values: tuple[str, ...]) -> str:
    rendered = ",".join(f"'{v}'" for v in values)
    return f"{column} IN ({rendered})"


_CATEGORY_SQL = _in_check("category", INSTRUMENT_CATEGORIES)
_RESPONDENT_SQL = _in_check("respondent", INSTRUMENT_RESPONDENTS)
_SCORING_SQL = _in_check("scoring_type", INSTRUMENT_SCORING_TYPES)
_LOCALE_SQL = _in_check("locale", INSTRUMENT_LOCALES)


class Instrument(GlobalRecordMixin, Base):
    """System or clinic-owned instrument definition."""

    __tablename__ = "instrument"
    __table_args__ = (
        CheckConstraint(_CATEGORY_SQL, name="ck_instrument__category"),
        CheckConstraint(_RESPONDENT_SQL, name="ck_instrument__respondent"),
        CheckConstraint(_SCORING_SQL, name="ck_instrument__scoring_type"),
        CheckConstraint("max_score >= min_score", name="ck_instrument__score_range"),
        CheckConstraint(
            "mcid IS NULL OR mcid > 0",
            name="ck_instrument__mcid",
        ),
        UniqueConstraint(
            "scope_clinic_id",
            "code",
            name="uq_instrument__scope_clinic_id__code",
        ),
        Index("ix_instrument__code", "code"),
        Index("ix_instrument__clinic_id__category", "clinic_id", "category"),
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
    code: Mapped[str] = mapped_column(
        String(40, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    respondent: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_type: Mapped[str] = mapped_column(String(30), nullable=False)
    min_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    max_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mcid: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    license_note: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    versions: Mapped[list[InstrumentVersion]] = relationship(
        "InstrumentVersion",
        back_populates="instrument",
        order_by="InstrumentVersion.effective_from.desc()",
        lazy="raise",
    )


class InstrumentVersion(
    SurrogatePkMixin,
    PublicIdMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    Base,
):
    """One versioned scoring definition for an instrument."""

    __tablename__ = "instrument_version"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "version",
            name="uq_instrument_version__instrument_id__version",
        ),
        Index(
            "ix_instrument_version__instrument_id__is_current",
            "instrument_id",
            "is_current",
        ),
    )

    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    instrument_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("instrument.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(20, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    scoring_config: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)

    instrument: Mapped[Instrument] = relationship(
        "Instrument",
        back_populates="versions",
        lazy="raise",
    )
    items: Mapped[list[InstrumentItem]] = relationship(
        "InstrumentItem",
        back_populates="instrument_version",
        order_by="InstrumentItem.position",
        lazy="raise",
    )
    options: Mapped[list[InstrumentOption]] = relationship(
        "InstrumentOption",
        back_populates="instrument_version",
        order_by="InstrumentOption.position",
        lazy="raise",
    )
    translations: Mapped[list[InstrumentTranslation]] = relationship(
        "InstrumentTranslation",
        back_populates="instrument_version",
        lazy="raise",
    )


class InstrumentItem(GlobalRecordMixin, Base):
    __tablename__ = "instrument_item"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_instrument_item__position"),
        CheckConstraint("weight > 0", name="ck_instrument_item__weight"),
        UniqueConstraint(
            "instrument_version_id",
            "position",
            name="uq_instrument_item__version__position",
        ),
        UniqueConstraint(
            "instrument_version_id",
            "code",
            name="uq_instrument_item__version__code",
        ),
    )

    instrument_version_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "instrument_version.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    code: Mapped[str] = mapped_column(
        String(40, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    subscale: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_reverse_scored: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1"),
        server_default="1.00",
    )

    instrument_version: Mapped[InstrumentVersion] = relationship(
        "InstrumentVersion",
        back_populates="items",
        lazy="raise",
    )


class InstrumentOption(GlobalRecordMixin, Base):
    __tablename__ = "instrument_option"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_instrument_option__position"),
        UniqueConstraint(
            "instrument_version_id",
            "scope_item_id",
            "position",
            name="uq_instrument_option__version__scope_item__position",
        ),
        UniqueConstraint(
            "instrument_version_id",
            "scope_item_id",
            "value",
            name="uq_instrument_option__version__scope_item__value",
        ),
    )

    instrument_version_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "instrument_version.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )
    item_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "instrument_item.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=True,
    )
    scope_item_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(item_id, 0)", persisted=True),
        nullable=False,
    )
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    instrument_version: Mapped[InstrumentVersion] = relationship(
        "InstrumentVersion",
        back_populates="options",
        lazy="raise",
    )


class InstrumentTranslation(GlobalRecordMixin, Base):
    __tablename__ = "instrument_translation"
    __table_args__ = (
        CheckConstraint(_LOCALE_SQL, name="ck_instrument_translation__locale"),
        CheckConstraint(
            "NOT (item_id IS NOT NULL AND option_id IS NOT NULL)",
            name="ck_instrument_translation__target",
        ),
        UniqueConstraint(
            "instrument_version_id",
            "scope_item_id",
            "scope_option_id",
            "locale",
            name="uq_instrument_translation__version__scopes__locale",
        ),
    )

    instrument_version_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "instrument_version.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )
    item_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "instrument_item.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=True,
    )
    option_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "instrument_option.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=True,
    )
    scope_item_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(item_id, 0)", persisted=True),
        nullable=False,
    )
    scope_option_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(option_id, 0)", persisted=True),
        nullable=False,
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)

    instrument_version: Mapped[InstrumentVersion] = relationship(
        "InstrumentVersion",
        back_populates="translations",
        lazy="raise",
    )
