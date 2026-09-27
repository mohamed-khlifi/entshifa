"""Canonical hash of a finalized document snapshot."""

from __future__ import annotations

import hashlib
import json
from typing import Any

VERSION = "1.0.0"
REFERENCE = (
    "SHA-256 over canonical JSON (sorted keys, UTF-8) of the frozen snapshot "
    "so a finalized document can be reproduced and compared (architecture §25.12)."
)


def content_hash(snapshot: dict[str, Any]) -> str:
    """Hex SHA-256 of the snapshot. Key order does not change the digest."""

    payload = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
