"""Exam-shape rules that are not a score. Codes stay in the catalog."""

from __future__ import annotations

from ent.features.laryngoscopy.constants import (
    CONSISTENCY_CODES,
    FINDINGS_FOR_STATUS,
    LESION_FINDINGS,
    MIDLINE_STRUCTURE_CODES,
    REINKE_CODE,
    RESIDUE_SITE_CODES,
    SIDED_STRUCTURE_CODES,
    STRUCTURE_CODES,
    VF_SURFACES,
    VF_THIRDS,
    VOCAL_FOLD_CODE,
)
from ent.features.laryngoscopy.exceptions import (
    LaryngoscopyExamError,
    LaryngoscopyFindingError,
    LaryngoscopyStructureError,
)
from ent.features.laryngoscopy.schemas.requests import (
    LaryngoscopyCreate,
    LaryngoscopyUpdate,
    VocalFoldLesionWrite,
    VocalFoldWrite,
)

_STRUCTURES = frozenset(STRUCTURE_CODES)
_THIRDS = frozenset(VF_THIRDS)
_SURFACES = frozenset(VF_SURFACES)
_CONSISTENCIES = frozenset(CONSISTENCY_CODES)
_RESIDUE = frozenset(RESIDUE_SITE_CODES)
Write = LaryngoscopyCreate | LaryngoscopyUpdate


def validate_exam(body: Write) -> None:
    """Reject a fold, structure, lesion or FEES block the catalog does not allow."""

    _fold("right", body.vocal_fold_right)
    _fold("left", body.vocal_fold_left)
    _structures(body)
    _lesions(body.lesions)
    _fees(body)


def _fold(side: str, fold: VocalFoldWrite) -> None:
    immobile = fold.mobility == "immobile"
    if immobile and fold.position is None:
        raise LaryngoscopyExamError(reason="position_required", item=side)
    if not immobile and fold.position is not None:
        raise LaryngoscopyExamError(reason="position_unexpected", item=side)


def _structures(body: Write) -> None:
    seen: set[tuple[str, str]] = set()
    for item in body.structures:
        code = item.body_site_code
        laterality = item.laterality.value
        if code not in _STRUCTURES:
            raise LaryngoscopyStructureError(body_site_code=code, reason="unknown_site")
        if code in MIDLINE_STRUCTURE_CODES and laterality not in {"midline", "na"}:
            raise LaryngoscopyStructureError(body_site_code=code, reason="laterality")
        if code in SIDED_STRUCTURE_CODES and laterality not in {"right", "left"}:
            raise LaryngoscopyStructureError(body_site_code=code, reason="laterality")
        key = (code, laterality)
        if key in seen:
            raise LaryngoscopyStructureError(body_site_code=code, reason="duplicate")
        seen.add(key)
        if item.finding_code not in FINDINGS_FOR_STATUS[item.status]:
            raise LaryngoscopyFindingError(
                finding_code=item.finding_code,
                status=item.status,
            )


def _lesions(lesions: list[VocalFoldLesionWrite]) -> None:
    for lesion in lesions:
        if lesion.finding_code not in LESION_FINDINGS:
            raise LaryngoscopyFindingError(
                finding_code=lesion.finding_code,
                status="abnormal",
            )
        if lesion.third_code not in _THIRDS or lesion.surface_code not in _SURFACES:
            raise LaryngoscopyExamError(reason="lesion_site", item=VOCAL_FOLD_CODE)
        reinke = lesion.finding_code == REINKE_CODE
        if reinke and lesion.reinke_grade is None:
            raise LaryngoscopyExamError(reason="reinke_grade_required")
        if not reinke and lesion.reinke_grade is not None:
            raise LaryngoscopyExamError(reason="reinke_grade_unexpected")


def _fees(body: Write) -> None:
    fees = body.fees
    if fees is None:
        return
    if not fees.consistencies:
        raise LaryngoscopyExamError(reason="consistency_required")
    unknown = [code for code in fees.consistencies if code not in _CONSISTENCIES]
    if unknown:
        raise LaryngoscopyExamError(reason="consistency", item=unknown[0])
    residue = [code for code in fees.residue_site_codes if code not in _RESIDUE]
    if residue:
        raise LaryngoscopyExamError(reason="residue", item=residue[0])
