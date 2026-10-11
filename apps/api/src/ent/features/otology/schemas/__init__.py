"""Otology request and response schemas."""

from ent.features.otology.schemas.requests import (
    EarDeviceStatusUpdate,
    OtologyCreate,
    OtologyUpdate,
)
from ent.features.otology.schemas.responses import EarDeviceRead, OtologyExamRead

__all__ = [
    "EarDeviceRead",
    "EarDeviceStatusUpdate",
    "OtologyCreate",
    "OtologyExamRead",
    "OtologyUpdate",
]
