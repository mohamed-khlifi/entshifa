"""Shared document mapping and placeholder checks."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from ent.core.errors.exceptions import (
    DocumentSyntaxError,
    DocumentTemplateError,
    ValidationError,
)
from ent.core.schemas.base import PageMeta, PageSchema
from ent.engines.documents.placeholders import missing_required
from ent.features.documents.constants import RTL_LOCALES
from ent.features.documents.models import (
    Document,
    DocumentTemplate,
    DocumentTemplateVersion,
)
from ent.features.documents.schemas.requests import DocumentTemplateCreate
from ent.features.documents.schemas.responses import DocumentRead, DocumentTemplateRead

PLACEHOLDER_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9]*(\.[A-Za-z][A-Za-z0-9]*)*$")


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def placeholder_dict(body: DocumentTemplateCreate) -> dict[str, Any]:
    return {
        key: {"type": spec.type, "required": spec.required}
        for key, spec in body.placeholders.items()
    }


def require_placeholder_keys(placeholders: dict[str, Any]) -> None:
    for key in placeholders:
        if PLACEHOLDER_KEY.match(key) is None:
            raise ValidationError(reason="placeholder", name=key)


def assert_direction(locale: str, direction: str) -> None:
    expected = "rtl" if locale in RTL_LOCALES else "ltr"
    if direction != expected:
        raise ValidationError(reason="direction", locale=locale)


def raise_placeholder(issue: Any) -> None:
    if issue.reason == "undeclared":
        raise DocumentTemplateError(name=issue.name)
    raise DocumentSyntaxError(reason=issue.reason, line=issue.line)


def require_data(placeholders: dict[str, Any], data: dict[str, Any]) -> None:
    missing = missing_required(placeholders, data)
    if missing:
        raise ValidationError(reason="placeholder_data", name=missing[0])


def document_title(version: DocumentTemplateVersion) -> str:
    raw = (
        version.page_setup.get("title")
        if isinstance(version.page_setup, dict)
        else None
    )
    if not isinstance(raw, str) or not raw.strip():
        raise ValidationError(reason="title")
    return raw.strip()[:200]


def template_read(row: DocumentTemplate) -> DocumentTemplateRead:
    return DocumentTemplateRead(
        public_id=row.public_id,
        code=row.code,
        category=row.category,
        is_system=row.is_system,
        is_active=row.is_active,
    )


def document_read(
    row: Document, patient_public_id: str, template_code: str
) -> DocumentRead:
    return DocumentRead(
        public_id=row.public_id,
        patient_public_id=patient_public_id,
        template_code=template_code,
        category=row.category,
        locale=row.locale,
        title=row.title,
        status=row.status,
        content_hash=row.content_hash,
        finalized_at=row.finalized_at,
    )


def page(
    items: list[Any],
    *,
    total: int | None,
    limit: int,
    offset: int | None,
) -> PageSchema[Any]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset),
    )


def concept_displays(
    labels: dict[int, tuple[str, str, str | None]],
    concept_ids: list[int],
) -> list[str]:
    names: list[str] = []
    for concept_id in concept_ids:
        found = labels.get(concept_id)
        if found is None or not found[2]:
            continue
        names.append(found[2])
    return names
