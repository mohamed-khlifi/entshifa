"""Known-answer checks for the anonymized development dump transforms."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ent.core.privacy.anonymize import anonymize_row, build_offsets, offset_days


def test_offset_is_stable_nonzero_and_bounded() -> None:
    first = offset_days("01ARZ3NDEKTSV4RRFFQ69G5FAV")
    assert first == offset_days("01ARZ3NDEKTSV4RRFFQ69G5FAV")
    assert first != 0
    assert -60 <= first <= 60


def test_patient_dates_shift_together_and_identifiers_are_scrubbed() -> None:
    birth = date(1980, 4, 2)
    start = datetime(2026, 9, 1, 9, 0, 0)
    patients = [{"id": 7, "public_id": "01PATIENTPUBLICID0000000001"}]
    offsets = build_offsets(patients)
    shift = timedelta(days=offsets[7])

    patient = anonymize_row(
        "patient",
        {
            "id": 7,
            "public_id": "01PATIENTPUBLICID0000000001",
            "first_name": "Bén",
            "last_name": "Alï",
            "email": "ben.ali@example.com",
            "phone_primary": "+21612345678",
            "mrn": "MRN-SECRET",
            "birth_date": birth,
            "name_normalized": "ben ali",
            "created_at": datetime(2026, 1, 1, 0, 0, 0),
        },
        offsets=offsets,
        password_hash="hash",
    )
    appointment = anonymize_row(
        "appointment",
        {
            "id": 3,
            "public_id": "01APPOINTMENTPUBLICID000001",
            "patient_id": 7,
            "starts_at": start,
            "ends_at": start + timedelta(minutes=30),
            "reason_text": "secret complaint",
            "created_at": datetime(2026, 1, 1, 0, 0, 0),
        },
        offsets=offsets,
        password_hash="hash",
    )

    assert patient["first_name"] == "Anon"
    assert "Alï" not in str(patient["last_name"])
    assert patient["email"].endswith("@invalid.example")
    assert patient["phone_primary"] == "+33000000000"
    assert patient["mrn"] != "MRN-SECRET"
    assert patient["birth_date"] == birth + shift
    assert patient["created_at"] == datetime(2026, 1, 1, 0, 0, 0)
    assert "ben ali" not in patient["name_normalized"]
    assert appointment["starts_at"] == start + shift
    assert appointment["ends_at"] - appointment["starts_at"] == timedelta(minutes=30)
    assert appointment["reason_text"] == "redacted"


def test_password_and_audit_payloads_are_replaced() -> None:
    row = anonymize_row(
        "user",
        {
            "id": 1,
            "public_id": "01USERPUBLICID000000000001",
            "email": "admin@demo.entshifa.local",
            "password_hash": "old-hash",
            "mfa_secret": b"secret",
            "first_name": "Amina",
        },
        offsets={},
        password_hash="dev-hash",
    )
    audit = anonymize_row(
        "audit_log",
        {
            "id": 9,
            "public_id": "01AUDITPUBLICID00000000001",
            "patient_id": None,
            "before_json": {"last_name": "Alï"},
            "ip_address": b"\x7f\x00\x00\x01",
            "user_agent": "Mozilla",
            "reason": "break glass",
        },
        offsets={7: 3},
        password_hash="dev-hash",
    )
    assert row["password_hash"] == "dev-hash"
    assert row["mfa_secret"] is None
    assert row["email"].endswith("@invalid.example")
    assert audit["before_json"] == {"redacted": True}
    assert audit["ip_address"] is None
    assert audit["user_agent"] == "redacted"
    assert audit["reason"] == "redacted"


def test_observation_free_text_dates_and_qualifiers_are_scrubbed() -> None:
    patients = [{"id": 7, "public_id": "01PATIENTPUBLICID0000000001"}]
    offsets = build_offsets(patients)
    effective = datetime(2026, 3, 1, 8, 0, 0)
    row = anonymize_row(
        "observation",
        {
            "id": 1,
            "public_id": "01OBSERVATIONPUBLICID000001",
            "patient_id": 7,
            "value_text": "secret finding",
            "effective_at": effective,
            "qualifiers": {"size_mm": 12},
            "created_at": datetime(2026, 1, 1, 0, 0, 0),
        },
        offsets=offsets,
        password_hash="hash",
    )
    assert row["value_text"] == "redacted"
    assert row["qualifiers"] == {"redacted": True}
    assert row["effective_at"] == effective + timedelta(days=offsets[7])
    assert row["created_at"] == datetime(2026, 1, 1, 0, 0, 0)
