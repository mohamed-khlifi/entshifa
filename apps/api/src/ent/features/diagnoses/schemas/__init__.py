"""Diagnosis schemas."""

from ent.features.diagnoses.schemas.requests import (
    DiagnosisFavoriteReplace,
    DiagnosisWrite,
)
from ent.features.diagnoses.schemas.responses import (
    DiagnosisFavoriteRead,
    DiagnosisRead,
)

__all__ = [
    "DiagnosisFavoriteRead",
    "DiagnosisFavoriteReplace",
    "DiagnosisRead",
    "DiagnosisWrite",
]
