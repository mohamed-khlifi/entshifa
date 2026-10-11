"""Exam-shape rules reject a fold, lesion or FEES block the catalog does not allow."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ent.features.laryngoscopy.constants import REINKE_CODE, VOCAL_FOLD_CODE
from ent.features.laryngoscopy.exceptions import (
    LaryngoscopyExamError,
    LaryngoscopyFindingError,
    LaryngoscopyStructureError,
)
from ent.features.laryngoscopy.rules import validate_exam
from ent.features.laryngoscopy.schemas.requests import LaryngoscopyCreate


def _body(**overrides: object) -> LaryngoscopyCreate:
    payload: dict[str, object] = {
        "patient_public_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "performed_at": datetime(2026, 10, 11, 10, 0, tzinfo=UTC),
        "scope_type": "flexible_fiberoptic",
        "vocal_fold_right": {"mobility": "normal"},
        "vocal_fold_left": {"mobility": "normal"},
        "glottic_closure": "complete",
    }
    payload.update(overrides)
    return LaryngoscopyCreate.model_validate(payload)


def test_immobile_fold_requires_a_position() -> None:
    with pytest.raises(LaryngoscopyExamError) as caught:
        validate_exam(
            _body(vocal_fold_right={"mobility": "immobile", "position": None})
        )
    assert caught.value.context["reason"] == "position_required"
    assert caught.value.context["item"] == "right"


def test_mobile_fold_rejects_a_position() -> None:
    with pytest.raises(LaryngoscopyExamError) as caught:
        validate_exam(
            _body(vocal_fold_left={"mobility": "hypomobile", "position": "lateral"})
        )
    assert caught.value.context["reason"] == "position_unexpected"


def test_unknown_structure_and_status_mismatch_are_rejected() -> None:
    with pytest.raises(LaryngoscopyStructureError):
        validate_exam(
            _body(
                structures=[
                    {
                        "body_site_code": "ANAT.UNKNOWN",
                        "laterality": "midline",
                        "status": "normal",
                        "finding_code": "FIND.LARYNX.NORMAL",
                    }
                ]
            )
        )
    with pytest.raises(LaryngoscopyFindingError):
        validate_exam(
            _body(
                structures=[
                    {
                        "body_site_code": "ANAT.LARYNX.EPIGLOTTIS",
                        "laterality": "midline",
                        "status": "normal",
                        "finding_code": "FIND.LARYNX.EDEMA",
                    }
                ]
            )
        )


def test_reinke_grade_is_required_only_for_reinke_edema() -> None:
    lesion = {
        "laterality": "right",
        "third_code": "QUAL.VF.THIRD.ANTERIOR",
        "surface_code": "QUAL.VF.SURFACE.FREE_EDGE",
        "finding_code": REINKE_CODE,
    }
    with pytest.raises(LaryngoscopyExamError) as caught:
        validate_exam(_body(lesions=[lesion]))
    assert caught.value.context["reason"] == "reinke_grade_required"
    validate_exam(_body(lesions=[{**lesion, "reinke_grade": 2}]))
    with pytest.raises(LaryngoscopyExamError) as unexpected:
        validate_exam(
            _body(
                lesions=[
                    {
                        **lesion,
                        "finding_code": "FIND.LARYNX.NODULE",
                        "reinke_grade": 1,
                    }
                ]
            )
        )
    assert unexpected.value.context["reason"] == "reinke_grade_unexpected"
    assert VOCAL_FOLD_CODE
