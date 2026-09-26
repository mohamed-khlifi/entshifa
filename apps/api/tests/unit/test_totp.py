"""TOTP helper known-answer check."""

from __future__ import annotations

import pyotp

from ent.core.security.totp import generate_totp_secret, verify_totp


def test_verify_totp_accepts_current_code() -> None:
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret=secret, code=code) is True


def test_verify_totp_rejects_garbage() -> None:
    secret = generate_totp_secret()
    assert verify_totp(secret=secret, code="000000") is False
