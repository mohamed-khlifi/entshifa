"""Custom SQLAlchemy column types (architecture §6 / §23)."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import CHAR, Numeric, String, TypeDecorator
from sqlalchemy.dialects.mysql import VARBINARY
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import composite

from ent.core.utils.ids import new_ulid

ULID_LENGTH = 26
LATERALITY_VALUES = frozenset({"right", "left", "bilateral", "midline", "na"})
_AESGCM_NONCE_BYTES = 12


class ULIDType(TypeDecorator[str]):
    """CHAR(26) ULID with case-sensitive collation; generates on insert if empty."""

    impl = CHAR(ULID_LENGTH, collation="utf8mb4_0900_as_cs")
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str:
        if value is None or value == "":
            return new_ulid()
        if len(value) != ULID_LENGTH:
            msg = f"ULID must be {ULID_LENGTH} characters, got {len(value)}"
            raise ValueError(msg)
        return value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        return value


class EncryptedString(TypeDecorator[str | None]):
    """Application-level AES-256-GCM ciphertext stored as VARBINARY."""

    impl = VARBINARY(255)
    cache_ok = True

    def process_bind_param(
        self,
        value: str | None,
        dialect: Dialect,
    ) -> bytes | None:
        if value is None:
            return None
        key = _field_encryption_key()
        nonce = os.urandom(_AESGCM_NONCE_BYTES)
        ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), None)
        return nonce + ciphertext

    def process_result_value(
        self,
        value: bytes | None,
        dialect: Dialect,
    ) -> str | None:
        if value is None:
            return None
        if len(value) <= _AESGCM_NONCE_BYTES:
            msg = "EncryptedString payload is too short"
            raise ValueError(msg)
        key = _field_encryption_key()
        nonce = value[:_AESGCM_NONCE_BYTES]
        ciphertext = value[_AESGCM_NONCE_BYTES:]
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")


class LateralityType(TypeDecorator[str]):
    """VARCHAR(10) laterality with the section-23 allowed set."""

    impl = String(10)
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if value not in LATERALITY_VALUES:
            allowed = ", ".join(sorted(LATERALITY_VALUES))
            msg = f"Invalid laterality {value!r}; expected one of: {allowed}"
            raise ValueError(msg)
        return value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        return value


@dataclass(frozen=True, slots=True)
class Quantity:
    """Clinical measurement: numeric value plus unit string (never translated)."""

    value: Decimal | None
    unit: str | None


def quantity_composite(value_column: Any, unit_column: Any) -> Any:
    """Map a value+unit column pair onto :class:`Quantity`."""

    return composite(Quantity, value_column, unit_column)


class QuantityValue(TypeDecorator[Decimal | None]):
    """DECIMAL storage for Quantity.value (exact clinical measurements)."""

    impl = Numeric(12, 3)
    cache_ok = True

    def process_bind_param(
        self,
        value: Decimal | float | int | str | None,
        dialect: Dialect,
    ) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))

    def process_result_value(
        self,
        value: Decimal | None,
        dialect: Dialect,
    ) -> Decimal | None:
        return value


def _field_encryption_key() -> bytes:
    """Derive a 32-byte AES key from FIELD_ENCRYPTION_KEY (any local string works)."""

    from ent.settings import get_settings

    raw = get_settings().field_encryption_key.encode("utf-8")
    return hashlib.sha256(raw).digest()
