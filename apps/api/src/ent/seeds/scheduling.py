"""Default appointment types per clinic (P1-07)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.features.scheduling.constants import DEFAULT_APPOINTMENT_TYPES
from ent.features.scheduling.models import AppointmentType
from ent.features.scheduling.repository import AppointmentTypeRepository


async def seed_appointment_types(
    session: AsyncSession,
    *,
    clinic_id: int,
    created_by_id: int | None,
) -> int:
    repo = AppointmentTypeRepository(session, clinic_id)
    created = 0
    for spec in DEFAULT_APPOINTMENT_TYPES:
        code = str(spec["code"])
        existing = await repo.get_by_code(code)
        if existing is not None:
            continue
        row = AppointmentType(
            clinic_id=clinic_id,
            code=code,
            name_key=spec["name_key"],
            default_duration_min=spec["default_duration_min"],
            color=spec["color"],
            requires_room=spec["requires_room"],
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        await repo.add(row)
        created += 1
    return created
