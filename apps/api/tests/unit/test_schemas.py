"""Unit tests for CamelModel and shared clinical value objects."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from ent.core.repository.pagination import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT, normalize_pagination
from ent.core.schemas.base import CamelModel, PageMeta, PageSchema, PaginationParams
from ent.core.schemas.common import (
    Attachment,
    CodeableConcept,
    Laterality,
    Period,
    Provenance,
    Quantity,
)


class _SampleModel(CamelModel):
    next_cursor: str | None = None
    is_primary: bool = False
    recorded_at: str | None = None


def test_camel_model_serializes_snake_to_camel() -> None:
    payload = _SampleModel(next_cursor="01JABC", is_primary=True, recorded_at="now")
    assert payload.model_dump(by_alias=True) == {
        "nextCursor": "01JABC",
        "isPrimary": True,
        "recordedAt": "now",
    }


def test_camel_model_accepts_camel_input() -> None:
    payload = _SampleModel.model_validate(
        {"nextCursor": "01JXYZ", "isPrimary": True},
    )
    assert payload.next_cursor == "01JXYZ"
    assert payload.is_primary is True


def test_page_schema_envelope_is_camel_case() -> None:
    page = PageSchema[str](
        items=["a"],
        page=PageMeta(total=1, limit=25, offset=0, next_cursor=None),
    )
    dumped = page.model_dump(by_alias=True)
    assert dumped["page"]["nextCursor"] is None
    assert dumped["page"]["limit"] == 25


def test_pagination_defaults_are_bounded() -> None:
    resolved = normalize_pagination(None)
    assert resolved.limit == DEFAULT_PAGE_LIMIT
    assert resolved.offset == 0
    assert resolved.cursor is None

    # Bypass schema ge/le so normalize_pagination clamping is exercised.
    clamped = normalize_pagination(
        PaginationParams.model_construct(limit=999, offset=10, cursor=None),
    )
    assert clamped.limit == MAX_PAGE_LIMIT
    assert clamped.offset == 10


def test_common_value_objects_round_trip() -> None:
    concept = CodeableConcept(concept_id="01JCONCEPT", code="otitis", display="Otitis")
    quantity = Quantity(value=Decimal("25.5"), unit="dB HL")
    period = Period(start=date(2024, 1, 1), end=date(2024, 12, 31))
    attachment = Attachment(id="01JATT", content_type="image/jpeg")
    provenance = Provenance(source="clinician", confirmed=True)

    assert concept.model_dump(by_alias=True)["conceptId"] == "01JCONCEPT"
    assert quantity.unit == "dB HL"
    assert period.start == date(2024, 1, 1)
    assert attachment.content_type == "image/jpeg"
    assert provenance.confirmed is True
    assert Laterality.RIGHT == "right"
