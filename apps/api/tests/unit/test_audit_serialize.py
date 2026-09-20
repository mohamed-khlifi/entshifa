"""Unit tests for audit serialization helpers."""

from __future__ import annotations

from ent.core.audit.serialize import row_to_audit_dict
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic


def test_row_to_audit_dict_redacts_nothing_on_clinic() -> None:
    clinic = Clinic(
        public_id=new_ulid(),
        name="Demo",
        slug="demo-audit",
        default_locale="en",
        supported_locales=["en"],
        timezone="UTC",
        country_code="FR",
        currency="EUR",
        settings={},
    )
    payload = row_to_audit_dict(clinic)
    assert payload["name"] == "Demo"
    assert payload["slug"] == "demo-audit"
