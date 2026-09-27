"""Document ORM models (architecture §25.12 / P1-09)."""

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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from ent.core.db.base import Base
from ent.core.db.mixins import (
    AuditMixin,
    ClinicalRecordMixin,
    GlobalRecordMixin,
    PublicIdMixin,
    SoftDeleteMixin,
    SurrogatePkMixin,
    TimestampMixin,
)
from ent.core.db.mysql_types import datetime6, mysql_json, unsigned_bigint
from ent.features.documents.constants import (
    DELIVERY_STATUSES,
    DOCUMENT_LOCALES,
    DOCUMENT_STATUSES,
    DOCUMENT_TEMPLATE_CATEGORIES,
    RECIPIENT_CHANNELS,
    RECIPIENT_TYPES,
)


def _medium_text() -> Any:
    return MEDIUMTEXT()  # type: ignore[no-untyped-call]


def _in_check(column: str, values: tuple[str, ...], *, nullable: bool = False) -> str:
    rendered = ",".join(f"'{value}'" for value in values)
    if nullable:
        return f"{column} IS NULL OR {column} IN ({rendered})"
    return f"{column} IN ({rendered})"


class DocumentTemplate(GlobalRecordMixin, Base):
    """Versioned print template. clinic_id is null for system templates."""

    __tablename__ = "document_template"
    __table_args__ = (
        CheckConstraint(
            _in_check("category", DOCUMENT_TEMPLATE_CATEGORIES),
            name="ck_document_template__category",
        ),
        CheckConstraint("engine IN ('html')", name="ck_document_template__engine"),
        UniqueConstraint(
            "scope_clinic_id",
            "code",
            name="uq_document_template__scope_clinic_id__code",
        ),
        Index("ix_document_template__code", "code"),
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
        String(60, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    engine: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="html",
        server_default="html",
    )
    placeholders: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
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


class DocumentTemplateVersion(
    SurrogatePkMixin,
    PublicIdMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    Base,
):
    """One locale of one template revision. ``version`` is the revision, not a lock."""

    __tablename__ = "document_template_version"
    __table_args__ = (
        CheckConstraint(
            _in_check("locale", DOCUMENT_LOCALES),
            name="ck_document_template_version__locale",
        ),
        CheckConstraint(
            "direction IN ('ltr','rtl')",
            name="ck_document_template_version__direction",
        ),
        UniqueConstraint(
            "document_template_id",
            "version",
            "locale",
            name="uq_document_template_version__template__version__locale",
        ),
    )

    clinic_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("clinic.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    document_template_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("document_template.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer(), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    header_html: Mapped[str] = mapped_column(_medium_text(), nullable=False)
    body_html: Mapped[str] = mapped_column(_medium_text(), nullable=False)
    footer_html: Mapped[str] = mapped_column(_medium_text(), nullable=False)
    css: Mapped[str] = mapped_column(_medium_text(), nullable=False)
    page_setup: Mapped[dict[str, Any]] = mapped_column(mysql_json(), nullable=False)
    direction: Mapped[str] = mapped_column(String(3), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)


class Document(ClinicalRecordMixin, Base):
    """Generated clinical document. Final rows are immutable."""

    __tablename__ = "document"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("category", DOCUMENT_TEMPLATE_CATEGORIES),
            name="ck_document__category",
        ),
        CheckConstraint(
            _in_check("locale", DOCUMENT_LOCALES),
            name="ck_document__locale",
        ),
        CheckConstraint(
            _in_check("status", DOCUMENT_STATUSES),
            name="ck_document__status",
        ),
        Index(
            "ix_document__clinic_id__patient_id__created_at",
            "clinic_id",
            "patient_id",
            "created_at",
        ),
        Index(
            "ix_document__clinic_id__category__status",
            "clinic_id",
            "category",
            "status",
        ),
    )

    patient_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("patient.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    encounter_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    template_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("document_template.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    template_version_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey(
            "document_template_version.id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    rendered_attachment_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        ForeignKey("attachment.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    content_snapshot: Mapped[dict[str, Any]] = mapped_column(
        mysql_json(),
        nullable=False,
    )
    body_override_html: Mapped[str | None] = mapped_column(
        _medium_text(), nullable=True
    )
    finalized_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    finalized_by_id: Mapped[int | None] = mapped_column(
        unsigned_bigint(),
        nullable=True,
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64, collation="utf8mb4_0900_as_cs"),
        nullable=True,
    )


class DocumentRecipient(ClinicalRecordMixin, Base):
    """Who a document is addressed to. Locale may differ from the clinic."""

    __tablename__ = "document_recipient"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("recipient_type", RECIPIENT_TYPES),
            name="ck_document_recipient__recipient_type",
        ),
        CheckConstraint(
            _in_check("channel", RECIPIENT_CHANNELS),
            name="ck_document_recipient__channel",
        ),
        CheckConstraint(
            _in_check("delivery_status", DELIVERY_STATUSES),
            name="ck_document_recipient__delivery_status",
        ),
        Index(
            "ix_document_recipient__clinic_id__document_id",
            "clinic_id",
            "document_id",
        ),
    )

    document_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        ForeignKey("document.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    recipient_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(190), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    delivery_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    error_text: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PhraseLibrary(ClinicalRecordMixin, Base):
    """Clinic or personal phrase. user_id is null for a shared clinic phrase."""

    __tablename__ = "phrase_library"
    __audit_writes__ = True
    __table_args__ = (
        CheckConstraint(
            _in_check("locale", DOCUMENT_LOCALES),
            name="ck_phrase_library__locale",
        ),
        UniqueConstraint(
            "clinic_id",
            "scope_user_id",
            "shortcut",
            "locale",
            name="uq_phrase_library__clinic__user__shortcut__locale",
        ),
    )

    user_id: Mapped[int | None] = mapped_column(unsigned_bigint(), nullable=True)
    scope_user_id: Mapped[int] = mapped_column(
        unsigned_bigint(),
        Computed("ifnull(user_id, 0)", persisted=True),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    shortcut: Mapped[str] = mapped_column(
        String(20, collation="utf8mb4_0900_as_cs"),
        nullable=False,
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    body: Mapped[str] = mapped_column(_medium_text(), nullable=False)
    usage_count: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
        server_default="0",
    )
