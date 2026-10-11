"""Closed values for the document engine (architecture §25.12)."""

from __future__ import annotations

DOCUMENT_TEMPLATE_CATEGORIES = (
    "consultation_report",
    "endoscopy_report",
    "audiology_report",
    "prescription",
    "certificate",
    "imaging_request",
    "lab_request",
    "referral_letter",
    "handout",
    "consent",
    "quote",
    "operative_note",
    "tumor_board",
    "patient_summary",
)

DOCUMENT_LOCALES = ("en", "fr", "ar")

DOCUMENT_STATUSES = ("draft", "final", "cancelled")

RECIPIENT_TYPES = ("patient", "referrer", "insurer", "other")

RECIPIENT_CHANNELS = ("print", "download")

DELIVERY_STATUSES = ("pending", "sent", "failed")

PLACEHOLDER_TYPES = (
    "string",
    "integer",
    "date",
    "code",
    "code_list",
    "text_list",
)

PATIENT_SUMMARY_CODE = "patient_summary"
CONSULTATION_REPORT_CODE = "consultation_report"
REFERRAL_LETTER_CODE = "referral_letter"
SICK_LEAVE_CODE = "sick_leave"
MEDICAL_CERTIFICATE_CODE = "medical_certificate"
IMAGING_REQUEST_CODE = "imaging_request"
LAB_REQUEST_CODE = "lab_request"

CLINICAL_TEMPLATE_CODES = (
    CONSULTATION_REPORT_CODE,
    REFERRAL_LETTER_CODE,
    SICK_LEAVE_CODE,
    MEDICAL_CERTIFICATE_CODE,
    IMAGING_REQUEST_CODE,
    LAB_REQUEST_CODE,
)

# Feature spec §14.4. MRI members must stay in engines.documents.safety.MRI_MODALITIES.
IMAGING_MODALITIES = (
    "ct_sinuses_noncontrast",
    "ct_temporal_bone_hr",
    "ct_neck_contrast",
    "mri_iac_gadolinium",
    "mri_neck",
    "pet_ct",
    "us_neck_fna",
    "panoramic_dental",
    "lateral_neck_adenoids",
)

LAB_PANELS = (
    "preoperative",
    "thyroid_calcitonin",
    "allergy_ige",
    "autoimmune_inner_ear",
    "sudden_hearing_loss_screen",
    "ear_discharge_culture",
    "hpv_status",
    "epistaxis_coagulation",
)

CERTIFICATE_PURPOSES = (
    "fitness",
    "swimming_tubes",
    "air_travel",
    "diving",
    "voice",
    "attendance",
    "other",
)

ABSENCE_TYPES = ("work", "school")
ABSENCE_REASON_MODES = ("medical_reasons", "diagnosis")
YES_NO = ("yes", "no")

RTL_LOCALES = frozenset({"ar"})
