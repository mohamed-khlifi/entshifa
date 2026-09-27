"""System reference data required in every environment (architecture §28)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.documents.seed import ensure_patient_summary_template
from ent.seeds.identity import ensure_all_permissions
from ent.seeds.reference_data import record_reference_data_version
from ent.seeds.terminology import TerminologySeedReport, seed_terminology
from ent.seeds.versions import (
    PERMISSIONS_VERSION,
    TEMPLATES_VERSION,
    TERMINOLOGY_VERSION,
)


@dataclass(frozen=True, slots=True)
class SystemSeedReport:
    permissions_created: int
    terminology: TerminologySeedReport
    reference_rows_created: int


async def seed_system(session: AsyncSession) -> SystemSeedReport:
    """Permissions, terminology, and system templates. Idempotent."""

    permissions_created = await ensure_all_permissions(session)
    terminology = await seed_terminology(session)
    await ensure_patient_summary_template(session)
    created = 0
    if await record_reference_data_version(
        session,
        dataset="permissions",
        version=PERMISSIONS_VERSION,
        notes="seed_system permissions",
    ):
        created += 1
    if await record_reference_data_version(
        session,
        dataset="terminology",
        version=TERMINOLOGY_VERSION,
        notes="seed_system terminology",
    ):
        created += 1
    if await record_reference_data_version(
        session,
        dataset="templates",
        version=TEMPLATES_VERSION,
        notes="seed_system patient summary template",
    ):
        created += 1
    return SystemSeedReport(
        permissions_created=permissions_created,
        terminology=terminology,
        reference_rows_created=created,
    )
