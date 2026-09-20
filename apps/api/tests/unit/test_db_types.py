"""Unit tests for EncryptedString, LateralityType, and Quantity."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.dialects import mysql

from ent.core.db.types import (
    EncryptedString,
    LateralityType,
    Quantity,
    QuantityValue,
    ULIDType,
)
from ent.core.utils.ids import new_ulid


def test_ulid_type_generates_on_empty_bind() -> None:
    dialect = mysql.dialect()
    produced = ULIDType().process_bind_param(None, dialect)
    assert produced is not None
    assert len(produced) == 26


def test_ulid_type_rejects_wrong_length() -> None:
    dialect = mysql.dialect()
    with pytest.raises(ValueError, match="ULID must be"):
        ULIDType().process_bind_param("too-short", dialect)


def test_ulid_type_accepts_valid_value() -> None:
    dialect = mysql.dialect()
    value = new_ulid()
    assert ULIDType().process_bind_param(value, dialect) == value


def test_laterality_type_accepts_allowed_values() -> None:
    dialect = mysql.dialect()
    for value in ("right", "left", "bilateral", "midline", "na"):
        assert LateralityType().process_bind_param(value, dialect) == value


def test_laterality_type_rejects_unknown() -> None:
    dialect = mysql.dialect()
    with pytest.raises(ValueError, match="Invalid laterality"):
        LateralityType().process_bind_param("both", dialect)


def test_encrypted_string_round_trip() -> None:
    dialect = mysql.dialect()
    column = EncryptedString()
    payload = column.process_bind_param("secret-mfa-seed", dialect)
    assert isinstance(payload, (bytes, bytearray))
    assert payload != b"secret-mfa-seed"
    assert column.process_result_value(payload, dialect) == "secret-mfa-seed"


def test_quantity_value_stores_decimal() -> None:
    dialect = mysql.dialect()
    column = QuantityValue()
    bound = column.process_bind_param(12.5, dialect)
    assert bound == Decimal("12.5")
    quantity = Quantity(value=bound, unit="dB HL")
    assert quantity.unit == "dB HL"
