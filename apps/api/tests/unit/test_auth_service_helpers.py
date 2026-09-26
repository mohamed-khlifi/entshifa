"""Unit tests for AuthService helpers."""

from __future__ import annotations

from ent.features.auth.service import _encode_ip


def test_encode_ip_variants() -> None:
    assert _encode_ip(None) is None
    assert _encode_ip("203.0.113.10") == b"\xcb\x00q\n"
    assert _encode_ip("::1") is not None
    assert _encode_ip("not-an-ip") is None
