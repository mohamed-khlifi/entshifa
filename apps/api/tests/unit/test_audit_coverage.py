"""Static audit coverage: clinical models and clinical read methods."""

from __future__ import annotations

import inspect
from collections.abc import Callable

from ent.core.db.base import Base
from ent.core.db.mixins import ClinicalRecordMixin
from ent.core.db.models_registry import ReferenceDataVersion as _registered
from ent.features.attachments.service import AttachmentService
from ent.features.documents.service import DocumentService
from ent.features.documents.templates.service import DocumentTemplateService
from ent.features.observations.service import ObservationService
from ent.features.patients.service import PatientService
from ent.features.scheduling.service import SchedulingService

_ = _registered


def test_clinical_record_models_audit_writes() -> None:
    missing = [
        cls.__name__
        for mapper in Base.registry.mappers
        if issubclass(cls := mapper.class_, ClinicalRecordMixin)
        and not getattr(cls, "__audit_writes__", False)
    ]
    assert missing == []


def _logs_access(func: Callable[..., object]) -> bool:
    source = inspect.getsource(func)
    return (
        "record_access" in source
        or "_access_patient" in source
        or "self._access(" in source
    )


def test_clinical_read_methods_record_access() -> None:
    expectations: tuple[tuple[type[object], tuple[str, ...]], ...] = (
        (PatientService, ("list_", "get_", "timeline")),
        (SchedulingService, ("list_", "get_")),
        (DocumentService, ("list_", "get_", "preview_", "download_")),
        (AttachmentService, ("list_", "get_", "request_download")),
        (DocumentTemplateService, ("list_", "get_")),
        (ObservationService, ("list_", "get_")),
    )
    missing: list[str] = []
    for cls, prefixes in expectations:
        for name, func in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("_") or not name.startswith(prefixes):
                continue
            if not _logs_access(func):
                missing.append(f"{cls.__name__}.{name}")
    assert missing == []
