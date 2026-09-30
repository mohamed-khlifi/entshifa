"""Pure transforms for an anonymized development dump (architecture §28).

Names, phones, identifiers and free text are replaced. Dates that belong to a
patient move by one stable per-patient offset so intervals stay intact.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from typing import Any

_CLINICAL_DATES = frozenset(
    {
        "birth_date",
        "onset_date",
        "resolved_date",
        "occurred_date",
        "started_on",
        "stopped_on",
        "ended_on",
        "starts_at",
        "ends_at",
        "arrived_at",
        "started_at",
        "ended_at",
        "signed_at",
        "captured_at",
        "finalized_at",
        "scheduled_for",
        "sent_at",
        "effective_at",
    }
)

_GLOBAL_SCRUB = frozenset(
    {
        "first_name",
        "last_name",
        "first_name_alt",
        "last_name_alt",
        "name",
        "legal_name",
        "email",
        "phone",
        "phone_primary",
        "phone_secondary",
        "referring_doctor_name",
        "referring_doctor_phone",
        "referring_doctor_email",
        "emergency_contact_name",
        "emergency_contact_phone",
        "guardian_name",
        "guardian_relation",
        "address_line1",
        "address_line2",
        "city",
        "postal_code",
        "occupation",
        "insurance_number",
        "tax_id",
        "registration_number",
        "website",
        "license_number",
        "note",
        "free_text",
        "free_text_name",
        "caption",
        "filename",
        "reason",
        "reason_text",
        "cancellation_reason",
        "user_agent",
        "title",
        "slug",
        "mrn",
        "value_text",
        "history_text",
        "assessment_text",
        "plan_text",
        "chief_complaint_summary",
        "duration_text",
        "body",
    }
)

_HTML_COLUMNS = frozenset(
    {
        "header_html",
        "body_html",
        "footer_html",
        "css",
        "body_override_html",
    }
)

_JSON_REDACT = frozenset(
    {"before_json", "after_json", "content_snapshot", "payload", "qualifiers"}
)


def offset_days(patient_public_id: str) -> int:
    """Stable non-zero shift in [-60, -1] or [1, 60] for one patient."""

    digest = hashlib.sha256(patient_public_id.encode("utf-8")).digest()
    span = int.from_bytes(digest[:2], "big") % 120
    if span < 60:
        return span - 60
    return span - 59


def build_offsets(patients: list[dict[str, Any]]) -> dict[int, int]:
    """Map internal patient id to that patient's date offset."""

    offsets: dict[int, int] = {}
    for row in patients:
        offsets[int(row["id"])] = offset_days(str(row["public_id"]))
    return offsets


def anonymize_row(
    table: str,
    row: dict[str, Any],
    *,
    offsets: dict[int, int],
    password_hash: str,
) -> dict[str, Any]:
    """Return a copy of ``row`` safe to keep in a development dump."""

    out = dict(row)
    offset = _offset_for(table, out, offsets)
    for column, value in list(out.items()):
        if value is None:
            continue
        if column == "password_hash":
            out[column] = password_hash
            continue
        if column in {"mfa_secret", "ip_address"}:
            out[column] = None
            continue
        if column in _JSON_REDACT:
            out[column] = {"redacted": True}
            continue
        if column in _HTML_COLUMNS:
            out[column] = "<p>redacted</p>"
            continue
        if table == "patient_identifier" and column == "value":
            out[column] = f"ID-{out.get('public_id', 'x')}"
            continue
        if column in _GLOBAL_SCRUB:
            out[column] = _replacement(table, column, out)
            continue
        if (
            offset is not None
            and column in _CLINICAL_DATES
            and isinstance(value, date | datetime)
        ):
            out[column] = value + timedelta(days=offset)
    if table == "patient":
        out["name_normalized"] = f"patient {str(out.get('public_id', 'x'))[:8].lower()}"
    return out


def _offset_for(
    table: str,
    row: dict[str, Any],
    offsets: dict[int, int],
) -> int | None:
    if table == "patient":
        patient_id = row.get("id")
    else:
        patient_id = row.get("patient_id")
    if patient_id is None:
        return None
    return offsets.get(int(patient_id))


def _replacement(table: str, column: str, row: dict[str, Any]) -> str:
    token = str(row.get("public_id") or row.get("id") or "x")
    if column in {"email", "referring_doctor_email"}:
        return f"user-{token.lower()}@invalid.example"
    if "phone" in column:
        return "+33000000000"
    if column in {"first_name", "first_name_alt"}:
        return "Anon"
    if column in {"last_name", "last_name_alt"}:
        return token[:8]
    if column == "mrn":
        return f"MRN{token[:8]}"
    if column == "slug":
        return f"clinic-{row.get('id', token[:8])}"
    if column in _HTML_COLUMNS:
        return "<p>redacted</p>"
    if table == "clinic" and column in {"name", "legal_name"}:
        return f"Clinic {row.get('id', '')}".strip()
    return "redacted"
