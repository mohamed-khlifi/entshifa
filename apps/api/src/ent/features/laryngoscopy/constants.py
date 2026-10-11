"""Stable laryngoscopy codes. Clinical math lives in ``engines.laryngoscopy``."""

from __future__ import annotations

from typing import Literal

SCOPE_TYPES = (
    "flexible_fiberoptic",
    "flexible_distal_chip",
    "rigid_70",
    "rigid_90",
)
MOBILITY_VALUES = ("normal", "hypomobile", "immobile", "paradoxical")
POSITION_VALUES = ("median", "paramedian", "intermediate", "lateral")
GLOTTIC_CLOSURE_VALUES = (
    "complete",
    "anterior_gap",
    "posterior_gap",
    "spindle",
    "hourglass",
    "irregular",
    "incomplete",
)
# # VERIFY: muscle-tension pattern names against the clinic's preferred scheme.
SUPRAGLOTTIC_VALUES = ("none", "anteroposterior", "mediolateral", "sphincteric")
SYMMETRY_VALUES = ("symmetric", "asymmetric")
PERIODICITY_VALUES = ("regular", "irregular")
AMPLITUDE_VALUES = ("normal", "reduced", "absent")
MUCOSAL_WAVE_VALUES = ("normal", "reduced", "absent")
PHASE_CLOSURE_VALUES = (
    "normal",
    "predominantly_open",
    "predominantly_closed",
    "always_open",
)
PHASE_SYMMETRY_VALUES = ("symmetric", "asymmetric")
VERTICAL_LEVEL_VALUES = ("on_plane", "off_plane_right_lower", "off_plane_left_lower")
NON_VIBRATING_VALUES = ("none", "right", "left", "bilateral")

PROCEDURE_CODE = "PROC.LARYNGOSCOPY"
VOCAL_FOLD_CODE = "ANAT.LARYNX.VOCAL_FOLD"
PAS_CODE = "SCORE.PAS"
REINKE_CODE = "FIND.LARYNX.REINKE_EDEMA"

RFS_ITEMS = (
    "subglottic_edema",
    "ventricular_obliteration",
    "erythema",
    "vocal_fold_edema",
    "diffuse_laryngeal_edema",
    "posterior_commissure_hypertrophy",
    "granuloma",
    "thick_endolaryngeal_mucus",
)
RFS_CONCEPT_CODES = {item: f"SCORE.RFS.{item.upper()}" for item in RFS_ITEMS}
RFS_ITEM_BY_CODE = {code: item for item, code in RFS_CONCEPT_CODES.items()}

GRBAS_ITEMS = ("grade", "roughness", "breathiness", "asthenia", "strain")
GRBAS_CONCEPT_CODES = {item: f"SCORE.GRBAS.{item.upper()}" for item in GRBAS_ITEMS}
GRBAS_ITEM_BY_CODE = {code: item for item, code in GRBAS_CONCEPT_CODES.items()}

STRUCTURES: tuple[tuple[str, str], ...] = (
    ("ANAT.NASAL_CAVITY", "sided"),
    ("ANAT.NASAL.NASOPHARYNX", "midline"),
    ("ANAT.LARYNX.VELUM", "midline"),
    ("ANAT.LARYNX.TONGUE_BASE", "midline"),
    ("ANAT.LARYNX.VALLECULA", "sided"),
    ("ANAT.LARYNX.EPIGLOTTIS", "midline"),
    ("ANAT.LARYNX.ARYEPIGLOTTIC_FOLD", "sided"),
    ("ANAT.LARYNX.ARYTENOID", "sided"),
    ("ANAT.LARYNX.PYRIFORM", "sided"),
    ("ANAT.LARYNX.POST_CRICOID", "midline"),
    ("ANAT.LARYNX.FALSE_CORD", "sided"),
    ("ANAT.LARYNX.VENTRICLE", "sided"),
    (VOCAL_FOLD_CODE, "sided"),
    ("ANAT.LARYNX.ANTERIOR_COMMISSURE", "midline"),
    ("ANAT.LARYNX.POSTERIOR_COMMISSURE", "midline"),
    ("ANAT.LARYNX.SUBGLOTTIS", "midline"),
    ("ANAT.LARYNX.TRACHEA", "midline"),
)
STRUCTURE_LATERALITY = dict(STRUCTURES)
STRUCTURE_CODES = tuple(code for code, _kind in STRUCTURES)
MIDLINE_STRUCTURE_CODES = frozenset(
    code for code, kind in STRUCTURES if kind == "midline"
)
SIDED_STRUCTURE_CODES = frozenset(code for code, kind in STRUCTURES if kind == "sided")

FINDING_NORMAL = "FIND.LARYNX.NORMAL"
FINDING_NOT_VISUALIZED = "FIND.LARYNX.NOT_VISUALIZED"
FINDING_UNKNOWN = "FIND.LARYNX.UNKNOWN"
ABNORMAL_FINDINGS = frozenset(
    {
        "FIND.LARYNX.EDEMA",
        "FIND.LARYNX.ERYTHEMA",
        "FIND.LARYNX.SECRETIONS",
        "FIND.LARYNX.POOLING",
        "FIND.LARYNX.PACHYDERMIA",
    }
)
LESION_FINDINGS = frozenset(
    {
        "FIND.LARYNX.NODULE",
        "FIND.LARYNX.POLYP",
        "FIND.LARYNX.CYST",
        REINKE_CODE,
        "FIND.LARYNX.GRANULOMA",
        "FIND.LARYNX.PAPILLOMA",
        "FIND.LARYNX.LEUKOPLAKIA",
        "FIND.LARYNX.ERYTHROPLAKIA",
        "FIND.LARYNX.ULCER",
        "FIND.LARYNX.MASS",
        "FIND.LARYNX.SULCUS",
        "FIND.LARYNX.SCAR",
        "FIND.LARYNX.WEB",
        "FIND.LARYNX.VARIX",
        "FIND.LARYNX.HEMORRHAGE",
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

VF_THIRDS = (
    "QUAL.VF.THIRD.ANTERIOR",
    "QUAL.VF.THIRD.MIDDLE",
    "QUAL.VF.THIRD.POSTERIOR",
)
VF_SURFACES = (
    "QUAL.VF.SURFACE.FREE_EDGE",
    "QUAL.VF.SURFACE.SUPERIOR",
)
# # VERIFY: IDDSI names before a signed FEES report prints a consistency.
CONSISTENCY_CODES = (
    "FEES.CONSISTENCY.THIN",
    "FEES.CONSISTENCY.NECTAR",
    "FEES.CONSISTENCY.HONEY",
    "FEES.CONSISTENCY.PUREE",
    "FEES.CONSISTENCY.SOLID",
)
RESIDUE_SITE_CODES = (
    "ANAT.LARYNX.VALLECULA",
    "ANAT.LARYNX.PYRIFORM",
    "ANAT.LARYNX.POST_CRICOID",
    VOCAL_FOLD_CODE,
    "ANAT.LARYNX.VESTIBULE",
)

ScopeType = Literal[
    "flexible_fiberoptic",
    "flexible_distal_chip",
    "rigid_70",
    "rigid_90",
]
MobilityValue = Literal["normal", "hypomobile", "immobile", "paradoxical"]
PositionValue = Literal["median", "paramedian", "intermediate", "lateral"]
GlotticClosure = Literal[
    "complete",
    "anterior_gap",
    "posterior_gap",
    "spindle",
    "hourglass",
    "irregular",
    "incomplete",
]
SupraglotticPattern = Literal["none", "anteroposterior", "mediolateral", "sphincteric"]
SymmetryValue = Literal["symmetric", "asymmetric"]
PeriodicityValue = Literal["regular", "irregular"]
AmplitudeValue = Literal["normal", "reduced", "absent"]
MucosalWave = Literal["normal", "reduced", "absent"]
PhaseClosure = Literal[
    "normal",
    "predominantly_open",
    "predominantly_closed",
    "always_open",
]
PhaseSymmetry = Literal["symmetric", "asymmetric"]
VerticalLevel = Literal["on_plane", "off_plane_right_lower", "off_plane_left_lower"]
NonVibratingSegment = Literal["none", "right", "left", "bilateral"]
StructureStatus = Literal["normal", "abnormal", "not_examined", "unknown"]
FoldSide = Literal["right", "left"]
