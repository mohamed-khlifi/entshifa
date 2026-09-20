"""Unit tests for argon2id password helpers."""

from __future__ import annotations

from ent.core.security.passwords import hash_password, verify_password


def test_hash_and_verify_round_trip() -> None:
    digest = hash_password("correct-horse-battery-staple")
    assert digest.startswith("$argon2id$")
    assert verify_password("correct-horse-battery-staple", digest)
    assert not verify_password("wrong-password", digest)
