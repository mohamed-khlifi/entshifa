"""Structure-list rules for otomicroscopy. Codes stay in the catalog."""

from __future__ import annotations

from collections.abc import Sequence

from ent.core.schemas.common import Laterality
from ent.features.otology.constants import (
    CANAL_ABNORMAL,
    CANAL_NORMAL,
    CANAL_NOT_VISUALIZED,
    CANAL_SITE,
    CANAL_UNKNOWN,
    SIDED_SUBTYPES,
    TM_ABNORMAL,
    TM_NORMAL,
    TM_NOT_VISUALIZED,
    TM_SITES,
    TM_UNKNOWN,
)
from ent.features.otology.exceptions import (
    OtologyFindingError,
    OtologyInvalidExamError,
    OtologyStructureError,
)
from ent.features.otology.schemas.requests import (
    OtologyCreate,
    OtologyStructureWrite,
    OtologyUpdate,
)

_SITES = frozenset((CANAL_SITE, *TM_SITES))
_CANAL_BY_STATUS = {
    "normal": frozenset({CANAL_NORMAL}),
    "abnormal": CANAL_ABNORMAL,
    "not_examined": frozenset({CANAL_NOT_VISUALIZED}),
    "unknown": frozenset({CANAL_UNKNOWN}),
}
_TM_BY_STATUS = {
    "normal": frozenset({TM_NORMAL}),
    "abnormal": TM_ABNORMAL,
    "not_examined": frozenset({TM_NOT_VISUALIZED}),
    "unknown": frozenset({TM_UNKNOWN}),
}

Write = OtologyCreate | OtologyUpdate


def validate_exam(body: Write) -> None:
    """Reject an incomplete tuning-fork set and a bilateral tube or wick."""

    tuning = (body.weber, body.rinne_right, body.rinne_left)
    if any(value is not None for value in tuning) and body.fork_frequency_hz is None:
        raise OtologyInvalidExamError(reason="fork_frequency_required")
    if (
        body.procedure is not None
        and body.procedure.subtype in SIDED_SUBTYPES
        and body.laterality not in {Laterality.RIGHT, Laterality.LEFT}
    ):
        raise OtologyInvalidExamError(reason="sided_laterality")
    validate_structures(body.structures)


def validate_structures(structures: Sequence[OtologyStructureWrite]) -> None:
    seen: set[tuple[str, str]] = set()
    for item in structures:
        code = item.body_site_code
        laterality = item.laterality.value
        if code not in _SITES:
            raise OtologyStructureError(body_site_code=code, reason="unknown_site")
        if laterality not in {"right", "left"}:
            raise OtologyStructureError(body_site_code=code, reason="laterality")
        key = (code, laterality)
        if key in seen:
            raise OtologyStructureError(body_site_code=code, reason="duplicate")
        seen.add(key)
        allowed = _CANAL_BY_STATUS if code == CANAL_SITE else _TM_BY_STATUS
        if item.finding_code not in allowed[item.status]:
            raise OtologyFindingError(
                finding_code=item.finding_code,
                status=item.status,
            )
