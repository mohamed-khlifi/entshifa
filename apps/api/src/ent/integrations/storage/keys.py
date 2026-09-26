"""Object key layout for clinical media (architecture §34)."""

from __future__ import annotations

import re

_SAFE_EXT = re.compile(r"^[a-z0-9]{1,10}$")
_SAFE_CATEGORY = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
_ULID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")

# Used when an attachment is clinic-scoped (logo, signature) without a patient.
CLINIC_SCOPED_PATIENT_SEGMENT = "_none"


def build_storage_key(
    *,
    clinic_public_id: str,
    patient_public_id: str | None,
    category: str,
    object_ulid: str,
    extension: str,
) -> str:
    """
    clinic/{clinicPublicId}/patient/{patientPublicId}/{category}/{ulid}.{ext}

    Paths are never sequential or guessable; clinic and patient use public ULIDs.
    """

    if not _ULID.match(clinic_public_id):
        msg = "clinic_public_id must be a ULID"
        raise ValueError(msg)
    if not _ULID.match(object_ulid):
        msg = "object_ulid must be a ULID"
        raise ValueError(msg)
    if not _SAFE_CATEGORY.match(category):
        msg = f"invalid attachment category: {category}"
        raise ValueError(msg)
    ext = extension.lower().lstrip(".")
    if not _SAFE_EXT.match(ext):
        msg = f"invalid file extension: {extension}"
        raise ValueError(msg)

    patient_segment = patient_public_id or CLINIC_SCOPED_PATIENT_SEGMENT
    if patient_segment != CLINIC_SCOPED_PATIENT_SEGMENT and not _ULID.match(
        patient_segment
    ):
        msg = "patient_public_id must be a ULID"
        raise ValueError(msg)

    return (
        f"clinic/{clinic_public_id}/patient/{patient_segment}/"
        f"{category}/{object_ulid}.{ext}"
    )


def variant_storage_key(original_key: str, *, variant: str) -> str:
    """Derive a sibling key for a media variant (thumb, preview, …)."""

    if "/" not in original_key or "." not in original_key.rsplit("/", 1)[-1]:
        msg = f"invalid storage key: {original_key}"
        raise ValueError(msg)
    if not re.match(r"^[a-z]{3,12}$", variant):
        msg = f"invalid variant: {variant}"
        raise ValueError(msg)
    directory, filename = original_key.rsplit("/", 1)
    stem, ext = filename.rsplit(".", 1)
    return f"{directory}/{stem}__{variant}.{ext}"
