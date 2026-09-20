"""Identifier helpers (architecture §6 utils/ids)."""

from __future__ import annotations

from ulid import ULID


def new_ulid() -> str:
    """Return a new Crockford-base32 ULID (26 chars, lexicographically sortable)."""

    return str(ULID())
