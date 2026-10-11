"""Structure-list rules for a nasal endoscopy. Codes stay in the catalog."""

from __future__ import annotations

from collections.abc import Sequence

from ent.features.endoscopy.constants import (
    ENDOSCOPY_STRUCTURE_CODES,
    FINDINGS_FOR_STATUS,
    MIDLINE_STRUCTURE_CODES,
    SIDED_STRUCTURE_CODES,
)
from ent.features.endoscopy.exceptions import (
    EndoscopyFindingError,
    EndoscopyStructureError,
)
from ent.features.endoscopy.schemas.requests import EndoscopyStructureWrite

_STRUCTURES = frozenset(ENDOSCOPY_STRUCTURE_CODES)


def validate_structures(structures: Sequence[EndoscopyStructureWrite]) -> None:
    """Reject unknown sites, the wrong side, duplicates, and mismatched findings."""

    seen: set[tuple[str, str]] = set()
    for item in structures:
        code = item.body_site_code
        laterality = item.laterality.value
        if code not in _STRUCTURES:
            raise EndoscopyStructureError(body_site_code=code, reason="unknown_site")
        if code in MIDLINE_STRUCTURE_CODES and laterality not in {"midline", "na"}:
            raise EndoscopyStructureError(body_site_code=code, reason="laterality")
        if code in SIDED_STRUCTURE_CODES and laterality not in {"right", "left"}:
            raise EndoscopyStructureError(body_site_code=code, reason="laterality")
        key = (code, laterality)
        if key in seen:
            raise EndoscopyStructureError(body_site_code=code, reason="duplicate")
        seen.add(key)
        allowed = FINDINGS_FOR_STATUS[item.status]
        if item.finding_code not in allowed:
            raise EndoscopyFindingError(
                finding_code=item.finding_code,
                status=item.status,
            )
