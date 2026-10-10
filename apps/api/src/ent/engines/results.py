"""Typed calculator output shared by every clinical engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Flag:
    """A named annotation on a calculation. Detail values stay machine-readable."""

    code: str
    detail: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class CalculationResult:
    """Reproducible calculator output (architecture section 8)."""

    code: str
    value: str
    unit: str | None
    inputs: Mapping[str, str]
    formula: str
    version: str
    reference: str
    flags: tuple[Flag, ...]
