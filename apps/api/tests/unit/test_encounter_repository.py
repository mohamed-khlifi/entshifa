"""Repository refuses to rewrite a signed encounter (P2-02)."""

from __future__ import annotations

from datetime import datetime

import pytest

from ent.core.utils.ids import new_ulid
from ent.features.encounters.exceptions import (
    EncounterInvalidTransitionError,
    EncounterLockedError,
)
from ent.features.encounters.models import Encounter
from ent.features.encounters.repository import EncounterRepository


def _repo() -> EncounterRepository:
    return EncounterRepository(session=None, clinic_id=1)  # type: ignore[arg-type]


def _encounter(status: str) -> Encounter:
    return Encounter(
        public_id=new_ulid(),
        clinic_id=1,
        status=status,
        version=1,
        started_at=datetime(2026, 6, 1, 9, 0, 0),
        encounter_type="consultation",
    )


def test_draft_text_can_change() -> None:
    encounter = _encounter("draft")
    _repo().apply_draft_changes(encounter, {"history_text": "onset yesterday"})
    assert encounter.history_text == "onset yesterday"


def test_signed_encounter_cannot_be_patched() -> None:
    encounter = _encounter("signed")
    with pytest.raises(EncounterLockedError) as raised:
        _repo().apply_draft_changes(encounter, {"history_text": "rewritten"})
    assert raised.value.code == "encounter.already_signed"
    assert encounter.history_text is None


def test_signing_is_only_legal_from_draft() -> None:
    repo = _repo()
    draft = _encounter("draft")
    signed_at = datetime(2026, 6, 1, 10, 0, 0)
    repo.mark_signed(
        draft,
        locked_hash="a" * 64,
        signed_at=signed_at,
        signed_by_id=7,
    )
    assert draft.status == "signed"
    assert draft.version == 2
    assert draft.locked_hash == "a" * 64
    with pytest.raises(EncounterLockedError):
        repo.mark_signed(
            draft,
            locked_hash="b" * 64,
            signed_at=signed_at,
            signed_by_id=7,
        )
    assert draft.locked_hash == "a" * 64


def test_addendum_is_refused_on_a_draft() -> None:
    with pytest.raises(EncounterInvalidTransitionError) as raised:
        _repo().mark_amended(_encounter("draft"), updated_by_id=7)
    assert raised.value.code == "encounter.invalid_transition"
    assert raised.value.http_status == 422


def test_signed_encounter_can_be_marked_amended() -> None:
    encounter = _encounter("signed")
    _repo().mark_amended(encounter, updated_by_id=9)
    assert encounter.status == "amended"
    assert encounter.version == 2
    assert encounter.updated_by_id == 9


def test_ip_encoding_accepts_v4_and_rejects_garbage() -> None:
    from ent.features.encounters.service import _encode_ip

    assert _encode_ip(None) is None
    assert _encode_ip("not-an-ip") is None
    assert _encode_ip("127.0.0.1") == b"\x7f\x00\x00\x01"
    packed = _encode_ip("::1")
    assert packed is not None
    assert len(packed) == 16
