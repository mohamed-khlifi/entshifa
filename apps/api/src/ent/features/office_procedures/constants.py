"""Closed values for short office procedures (feature spec §7.4).

Recall windows are the spans published in feature spec appendix C. The due
date itself is the date the clinician records. P3-08 moves these spans into
protocol rules.
"""

from __future__ import annotations

from typing import Literal

SHORT_OFFICE_SUBTYPES = (
    "epistaxis_management",
    "fine_needle_aspiration",
    "oral_pharyngeal_biopsy",
    "botulinum_injection",
    "peritonsillar_drainage",
    "nasal_fracture_reduction",
    "sialendoscopy",
)

SUBTYPE_EPISTAXIS = "epistaxis_management"
SUBTYPE_FNA = "fine_needle_aspiration"
SUBTYPE_BIOPSY = "oral_pharyngeal_biopsy"
SUBTYPE_BOTULINUM = "botulinum_injection"
SUBTYPE_PERITONSILLAR = "peritonsillar_drainage"
SUBTYPE_FRACTURE = "nasal_fracture_reduction"
SUBTYPE_SIALENDOSCOPY = "sialendoscopy"

PROC_EPISTAXIS = "PROC.EPISTAXIS_MANAGEMENT"
PROC_FNA = "PROC.FINE_NEEDLE_ASPIRATION"
PROC_BIOPSY = "PROC.ORAL_PHARYNGEAL_BIOPSY"
PROC_BOTULINUM = "PROC.BOTULINUM_INJECTION"
PROC_PERITONSILLAR = "PROC.PERITONSILLAR_DRAINAGE"
PROC_FRACTURE = "PROC.NASAL_FRACTURE_REDUCTION"
PROC_SIALENDOSCOPY = "PROC.SIALENDOSCOPY"

PROCEDURE_BY_SUBTYPE = {
    SUBTYPE_EPISTAXIS: PROC_EPISTAXIS,
    SUBTYPE_FNA: PROC_FNA,
    SUBTYPE_BIOPSY: PROC_BIOPSY,
    SUBTYPE_BOTULINUM: PROC_BOTULINUM,
    SUBTYPE_PERITONSILLAR: PROC_PERITONSILLAR,
    SUBTYPE_FRACTURE: PROC_FRACTURE,
    SUBTYPE_SIALENDOSCOPY: PROC_SIALENDOSCOPY,
}

# Appendix C: pack removal 48-72 h. The extra day is the window past the due date.
PACK_WINDOW_DAYS = 1
# Appendix C: nasal fracture splint removal day 7-10.
SPLINT_WINDOW_DAYS = 3
# Appendix C: office biopsy / specimen review 7-10 days. FNA uses the same span.
SPECIMEN_WINDOW_DAYS = 3
# Appendix C: sialendoscopy visit 2-4 weeks.
SIALENDOSCOPY_WINDOW_DAYS = 14

REASON_PACK = "office_pack_removal"
REASON_SPLINT = "office_splint_removal"
REASON_SPECIMEN = "office_specimen_review"
REASON_SIALENDOSCOPY = "office_sialendoscopy_review"

CONTENT_LOCALES = ("en", "fr", "ar")
SIDED = frozenset({SUBTYPE_EPISTAXIS, SUBTYPE_PERITONSILLAR, SUBTYPE_SIALENDOSCOPY})

EPISTAXIS_METHODS = (
    "silver_nitrate",
    "electrocautery",
    "anterior_pack",
    "posterior_pack",
    "balloon",
)
PACK_METHODS = frozenset({"anterior_pack", "posterior_pack", "balloon"})
# VERIFY: pack materials are not enumerated in the feature spec.
PACK_TYPES = ("merocel", "rapid_rhino", "ribbon_gauze")
# VERIFY: bleeding-site list is the usual office set; the spec says "location".
BLEEDING_SITES = (
    "little_area",
    "septum",
    "inferior_turbinate",
    "nasal_floor",
    "nasopharynx",
)
ANTICOAGULANT_STATUSES = ("yes", "no", "unknown")

# VERIFY: aspiration sites are not enumerated in the feature spec.
FNA_SITES = ("thyroid", "parotid", "submandibular", "neck_node", "other")
# VERIFY: biopsy sites and techniques are not enumerated; the spec names the procedure.
BIOPSY_SITES = (
    "oral_cavity",
    "tongue",
    "palate",
    "tonsil",
    "oropharynx",
    "hypopharynx",
)
BIOPSY_TECHNIQUES = ("punch", "incisional", "excisional")

BOTULINUM_INDICATIONS = (
    "spasmodic_dysphonia",
    "sialorrhea",
    "cricopharyngeal",
)
# VERIFY: muscle names follow the indication in feature spec §7.4, not a dose table.
MUSCLES_BY_INDICATION = {
    "spasmodic_dysphonia": frozenset({"thyroarytenoid", "lateral_cricoarytenoid"}),
    "sialorrhea": frozenset({"parotid", "submandibular"}),
    "cricopharyngeal": frozenset({"cricopharyngeus"}),
}
INJECTION_SIDES = ("right", "left", "bilateral", "midline")

DRAINAGE_METHODS = ("aspiration", "incision")
# VERIFY: splint names are not enumerated; the spec says "splint type".
SPLINT_TYPES = ("thermoplastic", "plaster", "denver", "tape")
GLANDS = ("parotid", "submandibular")
SIALENDOSCOPY_FINDINGS = ("stone", "stenosis", "mucus_plug")

ContentLocale = Literal["en", "fr", "ar"]
ShortSubtype = Literal[
    "epistaxis_management",
    "fine_needle_aspiration",
    "oral_pharyngeal_biopsy",
    "botulinum_injection",
    "peritonsillar_drainage",
    "nasal_fracture_reduction",
    "sialendoscopy",
]
