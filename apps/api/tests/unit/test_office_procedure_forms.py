"""Known shapes for the short office forms (feature spec §7.4, appendix C)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from ent.features.office_procedures.constants import (
    PACK_WINDOW_DAYS,
    REASON_PACK,
    REASON_SIALENDOSCOPY,
    REASON_SPECIMEN,
    REASON_SPLINT,
    SIALENDOSCOPY_WINDOW_DAYS,
    SPECIMEN_WINDOW_DAYS,
    SPLINT_WINDOW_DAYS,
)
from ent.features.office_procedures.schedule import (
    dates_before_procedure,
    planned_recalls,
    removal_due_date,
    result_due_date,
)
from ent.features.office_procedures.schemas.requests import (
    OfficeProcedureCreate,
    ShortProcedureWrite,
)

_ADAPTER = TypeAdapter(ShortProcedureWrite)
_PATIENT = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
_WHEN = datetime(2026, 6, 2, 9, 15)


def _body(detail: dict[str, object], **extra: object) -> OfficeProcedureCreate:
    payload: dict[str, object] = {
        "patientPublicId": _PATIENT,
        "performedAt": _WHEN,
        "laterality": "right",
        "anesthesia": "topical_spray",
        "detail": detail,
    }
    payload.update(extra)
    return OfficeProcedureCreate.model_validate(payload)


def test_cautery_has_no_pack_recall() -> None:
    body = _body(
        {
            "subtype": "epistaxis_management",
            "siteFound": True,
            "bleedingSite": "little_area",
            "method": "silver_nitrate",
            "systolicBp": 148,
            "diastolicBp": 86,
            "anticoagulantStatus": "yes",
            "adviceText": "Pinch and lean forward",
            "adviceLocale": "en",
        }
    )
    assert removal_due_date(body.detail) is None
    assert planned_recalls(body.detail, "right") == ()


def test_pack_records_removal_and_the_appendix_c_window() -> None:
    due = date(2026, 6, 4)
    body = _body(
        {
            "subtype": "epistaxis_management",
            "siteFound": False,
            "method": "anterior_pack",
            "packType": "merocel",
            "packRemovalDate": due.isoformat(),
            "systolicBp": 160,
            "diastolicBp": 90,
            "anticoagulantStatus": "no",
        }
    )
    assert removal_due_date(body.detail) == due
    recalls = planned_recalls(body.detail, "left")
    assert len(recalls) == 1
    assert recalls[0].reason_key == REASON_PACK
    assert recalls[0].due_on == due
    assert recalls[0].window_days == PACK_WINDOW_DAYS
    assert recalls[0].laterality == "left"


def test_pack_without_a_removal_date_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _body(
            {
                "subtype": "epistaxis_management",
                "siteFound": False,
                "method": "posterior_pack",
                "systolicBp": 120,
                "diastolicBp": 80,
                "anticoagulantStatus": "unknown",
            }
        )


def test_inverted_blood_pressure_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _body(
            {
                "subtype": "epistaxis_management",
                "siteFound": False,
                "method": "electrocautery",
                "systolicBp": 80,
                "diastolicBp": 90,
                "anticoagulantStatus": "no",
            }
        )


def test_biopsy_schedules_specimen_review() -> None:
    due = date(2026, 6, 9)
    body = _body(
        {
            "subtype": "oral_pharyngeal_biopsy",
            "site": "tongue",
            "technique": "incisional",
            "laboratoryText": "City lab",
            "laboratoryLocale": "en",
            "resultDueDate": due.isoformat(),
        },
        laterality="na",
    )
    assert result_due_date(body.detail) == due
    recalls = planned_recalls(body.detail, "na")
    assert recalls[0].reason_key == REASON_SPECIMEN
    assert recalls[0].window_days == SPECIMEN_WINDOW_DAYS


def test_splint_and_sialendoscopy_use_appendix_c_spans() -> None:
    splint = _body(
        {
            "subtype": "nasal_fracture_reduction",
            "splintType": "thermoplastic",
            "splintRemovalDate": "2026-06-09",
        },
        laterality="na",
        anesthesia="local_infiltration",
    )
    assert planned_recalls(splint.detail, "na")[0].reason_key == REASON_SPLINT
    assert planned_recalls(splint.detail, "na")[0].window_days == SPLINT_WINDOW_DAYS

    sial = _body(
        {
            "subtype": "sialendoscopy",
            "gland": "submandibular",
            "findings": ["stone", "stenosis"],
            "stoneRemoved": True,
            "followUpDate": "2026-06-16",
        }
    )
    assert planned_recalls(sial.detail, "right")[0].reason_key == REASON_SIALENDOSCOPY
    assert (
        planned_recalls(sial.detail, "right")[0].window_days
        == SIALENDOSCOPY_WINDOW_DAYS
    )


def test_stone_removed_requires_a_stone_finding() -> None:
    with pytest.raises(ValidationError):
        _body(
            {
                "subtype": "sialendoscopy",
                "gland": "parotid",
                "findings": ["mucus_plug"],
                "stoneRemoved": True,
                "followUpDate": "2026-06-16",
            }
        )


def test_botulinum_muscle_must_match_the_indication() -> None:
    with pytest.raises(ValidationError):
        _body(
            {
                "subtype": "botulinum_injection",
                "indication": "sialorrhea",
                "injections": [
                    {"muscle": "thyroarytenoid", "side": "right", "doseUnits": "2.5"}
                ],
            },
            laterality="bilateral",
        )
    accepted = _body(
        {
            "subtype": "botulinum_injection",
            "indication": "sialorrhea",
            "injections": [
                {"muscle": "parotid", "side": "right", "doseUnits": Decimal("10")},
                {
                    "muscle": "submandibular",
                    "side": "left",
                    "doseUnits": Decimal("5"),
                },
            ],
        },
        laterality="bilateral",
    )
    assert planned_recalls(accepted.detail, "bilateral") == ()


def test_peritonsillar_is_sided_and_has_no_automatic_recall() -> None:
    with pytest.raises(ValidationError):
        _body(
            {
                "subtype": "peritonsillar_drainage",
                "method": "aspiration",
                "volumeMl": "3.5",
                "cultureSent": True,
            },
            laterality="bilateral",
        )
    body = _body(
        {
            "subtype": "peritonsillar_drainage",
            "method": "incision",
            "volumeMl": "8",
            "cultureSent": False,
        }
    )
    assert planned_recalls(body.detail, "right") == ()


def test_a_due_date_before_the_procedure_is_named() -> None:
    body = _body(
        {
            "subtype": "fine_needle_aspiration",
            "site": "thyroid",
            "needleGauge": 25,
            "passes": 2,
            "ultrasoundGuided": True,
            "laboratoryText": "City lab",
            "laboratoryLocale": "fr",
            "resultDueDate": "2026-06-01",
        },
        laterality="midline",
    )
    assert dates_before_procedure(body.detail, date(2026, 6, 2)) == (
        "result_before_procedure"
    )


def test_stored_payload_round_trips() -> None:
    body = _body(
        {
            "subtype": "fine_needle_aspiration",
            "site": "other",
            "siteNote": "Right level II node",
            "siteNoteLocale": "en",
            "needleGauge": 23,
            "passes": 3,
            "ultrasoundGuided": False,
            "laboratoryText": "City lab",
            "laboratoryLocale": "en",
            "resultDueDate": "2026-06-09",
            "noteText": "Adequate sample",
            "noteLocale": "en",
        },
        laterality="right",
    )
    restored = _ADAPTER.validate_python(
        body.detail.model_dump(mode="json", by_alias=True)
    )
    assert restored.subtype == "fine_needle_aspiration"
    assert restored.site == "other"
