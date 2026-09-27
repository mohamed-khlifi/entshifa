"""Closed values for the document engine (architecture §25.12)."""

from __future__ import annotations

DOCUMENT_TEMPLATE_CATEGORIES = (
    "consultation_report",
    "endoscopy_report",
    "audiology_report",
    "prescription",
    "certificate",
    "imaging_request",
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

RTL_LOCALES = frozenset({"ar"})
