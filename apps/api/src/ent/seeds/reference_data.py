"""Idempotent reference_data_version rows (architecture §28)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.clinics.models import REFERENCE_DATASETS, ReferenceDataVersion


async def record_reference_data_version(
    session: AsyncSession,
    *,
    dataset: str,
    version: str,
    notes: str,
) -> bool:
    """Insert one applied revision. A repeat of the same pair is a no-op."""

    if dataset not in REFERENCE_DATASETS:
        msg = f"unknown reference dataset: {dataset}"
        raise ValueError(msg)
    existing = (
        await session.execute(
            select(ReferenceDataVersion.id).where(
                ReferenceDataVersion.dataset == dataset,
                ReferenceDataVersion.version == version,
                ReferenceDataVersion.deleted_at.is_(None),
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    applied_at = datetime.now(UTC).replace(tzinfo=None)
    session.add(
        ReferenceDataVersion(
            dataset=dataset,
            version=version,
            applied_at=applied_at,
            applied_by_id=None,
            notes=notes,
        ),
    )
    await session.flush()
    return True
