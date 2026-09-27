"""Local development seed entry point.

``seed_local_dev`` remains the demo clinic loader. The work is split into
``seed_system``, ``seed_demo`` and ``seed_test`` (architecture §28).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ent.seeds.identity import SeededUser
from ent.seeds.terminology import TerminologySeedReport

DEMO_CLINIC_SLUG = "demo-entshifa"
OTHER_CLINIC_SLUG = "demo-nord"


@dataclass(frozen=True, slots=True)
class LocalDevSeedReport:
    permissions_created: int
    clinics: int
    sites: int
    roles: int
    users: list[SeededUser]
    password: str
    terminology: TerminologySeedReport
    patients_created: int


async def seed_local_dev(session: AsyncSession) -> LocalDevSeedReport:
    """Load system reference data and the demo clinic."""

    from ent.seeds.demo import seed_demo

    return await seed_demo(session)
