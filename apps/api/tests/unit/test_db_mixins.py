"""Unit tests for section-23 mixins and ULID helpers."""

from __future__ import annotations

import concurrent.futures
import time

from sqlalchemy import inspect

from ent.core.db.mixins import (
    AuditMixin,
    ClinicalRecordMixin,
    PublicIdMixin,
    SoftDeleteMixin,
    SurrogatePkMixin,
    TenantMixin,
    TimestampMixin,
    VersionMixin,
)
from ent.core.utils.ids import new_ulid
from ent.features.clinics.models import Clinic, Site
from ent.features.users.models import User

SECTION_23_COLUMNS = frozenset(
    {
        "id",
        "public_id",
        "created_at",
        "updated_at",
        "created_by_id",
        "updated_by_id",
        "deleted_at",
        "deleted_by_id",
        "version",
    }
)


def _column_names(model: type[object]) -> set[str]:
    return {column.key for column in inspect(model).columns}


def test_clinic_mixin_columns_match_section_23() -> None:
    cols = _column_names(Clinic)
    assert cols >= SECTION_23_COLUMNS
    assert "clinic_id" not in cols


def test_site_mixin_columns_include_tenant() -> None:
    cols = _column_names(Site)
    assert SECTION_23_COLUMNS | {"clinic_id"} <= cols


def test_user_has_no_tenant_column() -> None:
    assert "clinic_id" not in _column_names(User)


def test_mixin_classes_expose_expected_attributes() -> None:
    assert hasattr(SurrogatePkMixin, "id")
    assert hasattr(PublicIdMixin, "public_id")
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")
    assert hasattr(AuditMixin, "created_by_id")
    assert hasattr(AuditMixin, "updated_by_id")
    assert hasattr(SoftDeleteMixin, "deleted_at")
    assert hasattr(SoftDeleteMixin, "deleted_by_id")
    assert hasattr(TenantMixin, "clinic_id")
    assert hasattr(VersionMixin, "version")
    assert issubclass(ClinicalRecordMixin, TenantMixin)


def test_ulid_length() -> None:
    value = new_ulid()
    assert len(value) == 26


def test_ulids_are_lexicographically_sortable_in_generation_order() -> None:
    values: list[str] = []
    for _ in range(20):
        values.append(new_ulid())
        time.sleep(0.002)
    assert values == sorted(values)


def test_ulids_unique_under_concurrent_generation() -> None:
    workers = 8
    per_worker = 250

    def _batch(_: int) -> list[str]:
        return [new_ulid() for _ in range(per_worker)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        batches = list(pool.map(_batch, range(workers)))

    all_ids = [item for batch in batches for item in batch]
    assert len(all_ids) == workers * per_worker
    assert len(set(all_ids)) == len(all_ids)
