"""Minimal domain event types (full bus/worker in P0-07)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Past-tense domain fact collected inside a unit of work."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
