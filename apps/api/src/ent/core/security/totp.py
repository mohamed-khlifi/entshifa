"""Optional TOTP second factor (architecture §29)."""

from __future__ import annotations

import pyotp

_ISSUER = "EntShifa"
_VALID_WINDOW = 1


def generate_totp_secret() -> str:
    return str(pyotp.random_base32())


def provisioning_uri(*, secret: str, account_name: str) -> str:
    return str(
        pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=_ISSUER)
    )


def verify_totp(*, secret: str, code: str) -> bool:
    normalized = code.strip().replace(" ", "")
    if not normalized.isdigit():
        return False
    return bool(pyotp.TOTP(secret).verify(normalized, valid_window=_VALID_WINDOW))
