"""Calendar arithmetic and structure rules for otology."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from ent.core.schemas.common import Laterality
from ent.features.otology.dates import add_days, add_months
from ent.features.otology.exceptions import (
    OtologyFindingError,
    OtologyInvalidExamError,
    OtologyStructureError,
)
from ent.features.otology.rules import validate_exam
from ent.features.otology.schemas.requests import OtologyCreate, OtologyStructureWrite


def test_add_months_clamps_the_day() -> None:
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2026, 8, 15), 6) == date(2027, 2, 15)


def test_add_days_crosses_the_month() -> None:
    assert add_days(date(2026, 1, 30), 3) == date(2026, 2, 2)


def _exam(**overrides: object) -> OtologyCreate:
    body: dict[str, object] = {
        "patient_public_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "performed_at": datetime(2026, 6, 2, 9, 15),
        "method": "microscopy",
        "laterality": Laterality.BILATERAL,
    }
    body.update(overrides)
    return OtologyCreate.model_validate(body)


def test_tuning_fork_requires_a_frequency() -> None:
    with pytest.raises(OtologyInvalidExamError) as exc:
        validate_exam(_exam(weber="midline"))
    assert exc.value.context["reason"] == "fork_frequency_required"


def test_tube_rejects_a_bilateral_side() -> None:
    with pytest.raises(OtologyInvalidExamError) as exc:
        validate_exam(
            _exam(
                procedure={
                    "subtype": "tube_insertion",
                    "tube_model": "shepard",
                    "effusion": "serous",
                }
            )
        )
    assert exc.value.context["reason"] == "sided_laterality"


def test_unknown_site_is_rejected() -> None:
    with pytest.raises(OtologyStructureError):
        validate_exam(
            _exam(
                structures=[
                    OtologyStructureWrite(
                        body_site_code="ANAT.NOSE",
                        laterality=Laterality.RIGHT,
                        status="normal",
                        finding_code="FIND.TM.NORMAL",
                        map_region_code="tm.canal",
                    )
                ]
            )
        )


def test_canal_finding_must_match_status() -> None:
    with pytest.raises(OtologyFindingError):
        validate_exam(
            _exam(
                structures=[
                    OtologyStructureWrite(
                        body_site_code="ANAT.EAR.CANAL",
                        laterality=Laterality.RIGHT,
                        status="normal",
                        finding_code="FIND.CANAL.WAX",
                        map_region_code="tm.canal",
                    )
                ]
            )
        )
