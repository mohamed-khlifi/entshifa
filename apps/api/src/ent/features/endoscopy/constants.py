"""Stable endoscopy codes. Clinical math lives in ``engines.endoscopy``."""

from __future__ import annotations

from typing import Literal

SCOPE_TYPES = ("flexible", "rigid_0", "rigid_30", "rigid_70")
POLYP_SCALES = ("meltzer", "lildholdt")

PROCEDURE_CODE = "PROC.NASAL_ENDOSCOPY"
POLYP_GRADE_CODE = "SCORE.POLYP.GRADE"
ADENOID_CODE = "SCORE.ADENOID.OBSTRUCTION"

LK_ITEMS = ("polyps", "edema", "discharge", "scarring", "crusting")
MODIFIED_LK_ITEMS = ("polyps", "edema", "discharge")
LK_CONCEPT_CODES = {
    "polyps": "SCORE.LK.POLYPS",
    "edema": "SCORE.LK.EDEMA",
    "discharge": "SCORE.LK.DISCHARGE",
    "scarring": "SCORE.LK.SCARRING",
    "crusting": "SCORE.LK.CRUSTING",
}
LK_ITEM_BY_CODE = {code: item for item, code in LK_CONCEPT_CODES.items()}

ENDOSCOPY_STRUCTURE_CODES = (
    "ANAT.NASAL.VESTIBULE",
    "ANAT.NASAL.VALVE",
    "ANAT.NASAL.SEPTUM",
    "ANAT.NASAL.INFERIOR_TURBINATE",
    "ANAT.NASAL.INFERIOR_MEATUS",
    "ANAT.NASAL.MIDDLE_TURBINATE",
    "ANAT.NASAL.MIDDLE_MEATUS",
    "ANAT.NASAL.UNCINATE",
    "ANAT.NASAL.BULLA",
    "ANAT.NASAL.SUPERIOR_TURBINATE",
    "ANAT.NASAL.SUPERIOR_MEATUS",
    "ANAT.NASAL.SPHENOETHMOIDAL_RECESS",
    "ANAT.NASAL.OLFACTORY_CLEFT",
    "ANAT.NASAL.NASOPHARYNX",
    "ANAT.NASAL.POST_FESS",
)
MIDLINE_STRUCTURE_CODES = frozenset(
    {
        "ANAT.NASAL.SEPTUM",
        "ANAT.NASAL.NASOPHARYNX",
        "ANAT.NASAL.POST_FESS",
    }
)
SIDED_STRUCTURE_CODES = frozenset(
    code for code in ENDOSCOPY_STRUCTURE_CODES if code not in MIDLINE_STRUCTURE_CODES
)

FINDING_NORMAL = "FIND.ENDO.NORMAL"
FINDING_NOT_VISUALIZED = "FIND.ENDO.NOT_VISUALIZED"
FINDING_UNKNOWN = "FIND.ENDO.UNKNOWN"
ABNORMAL_FINDINGS = frozenset(
    {
        "FIND.ENDO.POLYP",
        "FIND.ENDO.EDEMA",
        "FIND.ENDO.DISCHARGE",
        "FIND.ENDO.CRUST",
        "FIND.ENDO.SYNECHIA",
    }
)
FINDINGS_FOR_STATUS = {
    "normal": frozenset({FINDING_NORMAL}),
    "abnormal": ABNORMAL_FINDINGS,
    "not_examined": frozenset({FINDING_NOT_VISUALIZED}),
    "unknown": frozenset({FINDING_UNKNOWN}),
}
FINDING_CODES = frozenset(
    code for codes in FINDINGS_FOR_STATUS.values() for code in codes
)

ScopeType = Literal["flexible", "rigid_0", "rigid_30", "rigid_70"]
PolypScale = Literal["meltzer", "lildholdt"]
StructureStatus = Literal["normal", "abnormal", "not_examined", "unknown"]
