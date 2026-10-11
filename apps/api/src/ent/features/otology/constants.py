"""Closed values for otomicroscopy and office ear procedures (feature spec §7.3)."""

from __future__ import annotations

from typing import Literal

EXAM_METHODS = ("otoscopy", "microscopy")
WEBER_VALUES = ("midline", "lateralizes_right", "lateralizes_left")
RINNE_VALUES = ("positive", "negative")
FORK_FREQUENCIES = (256, 512)
MOBILITY_VALUES = ("normal", "reduced", "absent", "hypermobile")

OFFICE_SUBTYPES = (
    "wax_removal",
    "foreign_body",
    "wick",
    "tube_insertion",
    "tube_removal",
    "intratympanic_injection",
    "cavity_cleaning",
)
SIDED_SUBTYPES = frozenset(
    {
        "wick",
        "tube_insertion",
        "tube_removal",
        "intratympanic_injection",
        "cavity_cleaning",
    }
)

WAX_METHODS = ("microsuction", "curette", "irrigation")
WAX_COMPLETENESS = ("complete", "partial")
CANAL_CONDITIONS = ("clear", "residual_wax", "inflamed", "traumatized")
FOREIGN_BODY_METHODS = ("microsuction", "forceps", "irrigation", "hook")
TRAUMA_VALUES = ("none", "canal", "tympanic")
WICK_TYPES = ("pope", "ribbon", "merocel")
TUBE_MODELS = ("shepard", "armstrong", "t_tube", "bobbin", "paparella")
EFFUSION_VALUES = ("none", "serous", "mucoid", "purulent", "bloody")
TUBE_COMPLICATIONS = ("bleeding", "otorrhea", "vertigo", "perforation")
CAVITY_CONDITIONS = ("dry", "moist", "granulation", "debris", "exposed_structures")
DOSE_UNITS = ("mg", "mL")
CONTENT_LOCALES = ("en", "fr", "ar")

DEVICE_TYPES = ("ventilation_tube", "mastoid_cavity")
DEVICE_STATUSES = ("in_place", "blocked", "extruded", "removed", "retained")
OPEN_DEVICE_STATUSES = frozenset({"in_place", "blocked", "retained"})
CLOSED_DEVICE_STATUSES = frozenset({"extruded", "removed"})

STRUCTURE_STATUSES = ("normal", "abnormal", "not_examined", "unknown")
CANAL_SITE = "ANAT.EAR.CANAL"
TM_SITES = (
    "ANAT.TM.PF",
    "ANAT.TM.PT.AS",
    "ANAT.TM.PT.AI",
    "ANAT.TM.PT.PS",
    "ANAT.TM.PT.PI",
)
STRUCTURE_SITES = (CANAL_SITE, *TM_SITES)

CANAL_NORMAL = "FIND.CANAL.NORMAL"
CANAL_NOT_VISUALIZED = "FIND.CANAL.NOT_VISUALIZED"
CANAL_UNKNOWN = "FIND.CANAL.UNKNOWN"
CANAL_ABNORMAL = frozenset(
    {
        "FIND.CANAL.WAX",
        "FIND.CANAL.OTITIS_EXTERNA",
        "FIND.CANAL.FOREIGN_BODY",
        "FIND.CANAL.GRANULATION",
        "FIND.CANAL.EXOSTOSIS",
    }
)
TM_NORMAL = "FIND.TM.NORMAL"
TM_NOT_VISUALIZED = "FIND.TM.NOT_VISUALIZED"
TM_UNKNOWN = "FIND.TM.UNKNOWN"
TM_ABNORMAL = frozenset(
    {
        "FIND.TM.PERFORATION",
        "FIND.TM.RETRACTION",
        "FIND.TM.EFFUSION",
        "FIND.TM.CHOLESTEATOMA",
        "FIND.TM.TYMPANOSCLEROSIS",
        "FIND.TM.VENTILATION_TUBE",
    }
)
CHOLESTEATOMA_CODE = "FIND.TM.CHOLESTEATOMA"

PROC_OTOSCOPY = "PROC.OTOSCOPY"
PROC_MICROSCOPY = "PROC.OTOMICROSCOPY"
PROC_WAX = "PROC.CERUMEN_REMOVAL"
PROC_FOREIGN_BODY = "PROC.EAR_FOREIGN_BODY"
PROC_WICK = "PROC.EAR_WICK"
PROC_TUBE = "PROC.VENTILATION_TUBE"
PROC_TUBE_REMOVAL = "PROC.TUBE_REMOVAL"
PROC_INJECTION = "PROC.INTRATYMPANIC_INJECTION"
PROC_CAVITY = "PROC.CAVITY_CLEANING"

PROCEDURE_BY_SUBTYPE = {
    "wax_removal": PROC_WAX,
    "foreign_body": PROC_FOREIGN_BODY,
    "wick": PROC_WICK,
    "tube_insertion": PROC_TUBE,
    "tube_removal": PROC_TUBE_REMOVAL,
    "intratympanic_injection": PROC_INJECTION,
    "cavity_cleaning": PROC_CAVITY,
}

IT_DRUGS = (
    "DRUG.IT.DEXAMETHASONE",
    "DRUG.IT.METHYLPREDNISOLONE",
    "DRUG.IT.GENTAMICIN",
)

FLAG_TUBE = "ventilation_tube"
FLAG_CAVITY = "mastoid_cavity"
FLAG_CHOLESTEATOMA = "cholesteatoma"

REASON_TUBE_PATENCY = "otology_tube_patency"
REASON_TUBE_CHECK = "otology_tube_check"
REASON_WICK = "otology_wick_removal"
REASON_CAVITY = "otology_cavity_cleaning"
REASON_CANAL_INJURY = "otology_canal_injury"
TUBE_REASON_KEYS = frozenset({REASON_TUBE_PATENCY, REASON_TUBE_CHECK})

ExamMethod = Literal["otoscopy", "microscopy"]
WeberValue = Literal["midline", "lateralizes_right", "lateralizes_left"]
RinneValue = Literal["positive", "negative"]
MobilityValue = Literal["normal", "reduced", "absent", "hypermobile"]
StructureStatus = Literal["normal", "abnormal", "not_examined", "unknown"]
DeviceStatus = Literal["in_place", "blocked", "extruded", "removed", "retained"]
DeviceType = Literal["ventilation_tube", "mastoid_cavity"]
DoseUnit = Literal["mg", "mL"]
ContentLocale = Literal["en", "fr", "ar"]
