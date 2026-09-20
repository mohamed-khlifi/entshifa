"""Local development seed (identity, auth, and terminology)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.permissions import SYSTEM_ROLE_MATRIX
from ent.features.auth.models import Role
from ent.seeds.identity import (
    LOCAL_DEV_PASSWORD,
    SeededUser,
    ensure_all_permissions,
    ensure_clinic,
    ensure_role,
    ensure_site,
    ensure_user_with_role,
)
from ent.seeds.terminology import TerminologySeedReport, seed_terminology

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


async def seed_local_dev(session: AsyncSession) -> LocalDevSeedReport:
    permissions_created = await ensure_all_permissions(session)

    demo = await ensure_clinic(
        session,
        slug=DEMO_CLINIC_SLUG,
        name="Cabinet EntShifa Démo",
    )
    other = await ensure_clinic(
        session,
        slug=OTHER_CLINIC_SLUG,
        name="Clinique Nord (tenant B)",
    )

    await ensure_site(session, clinic=demo, name="Site principal", is_primary=True)
    await ensure_site(session, clinic=demo, name="Annexe", is_primary=False)
    await ensure_site(session, clinic=other, name="Site unique", is_primary=True)

    roles: dict[str, Role] = {}
    for role_code in SYSTEM_ROLE_MATRIX:
        roles[role_code] = await ensure_role(
            session,
            clinic=demo,
            code=role_code,
            name_key=f"role.{role_code}",
        )

    users: list[SeededUser] = []

    users.append(
        await ensure_user_with_role(
            session,
            clinic=demo,
            role=roles["clinic_admin"],
            email="admin@demo.entshifa.local",
            first_name="Amina",
            last_name="Admin",
        ),
    )

    doctor_names = [
        ("Sophie", "Bernard"),
        ("Karim", "Dupont"),
        ("Leila", "Moreau"),
        ("Thomas", "Petit"),
        ("Nadia", "Rousseau"),
    ]
    for index, (first, last) in enumerate(doctor_names, start=1):
        users.append(
            await ensure_user_with_role(
                session,
                clinic=demo,
                role=roles["doctor"],
                email=f"doctor{index}@demo.entshifa.local",
                first_name=first,
                last_name=last,
            ),
        )

    for index in range(1, 9):
        users.append(
            await ensure_user_with_role(
                session,
                clinic=demo,
                role=roles["assistant"],
                email=f"assistant{index}@demo.entshifa.local",
                first_name="Assistant",
                last_name=f"{index:02d}",
            ),
        )

    for index, (first, last) in enumerate(
        [("Marc", "Audio"), ("Yasmine", "Audi"), ("Paul", "Audiogram")],
        start=1,
    ):
        users.append(
            await ensure_user_with_role(
                session,
                clinic=demo,
                role=roles["audiology_technician"],
                email=f"audio{index}@demo.entshifa.local",
                first_name=first,
                last_name=last,
            ),
        )

    for index in range(1, 4):
        users.append(
            await ensure_user_with_role(
                session,
                clinic=demo,
                role=roles["read_only"],
                email=f"readonly{index}@demo.entshifa.local",
                first_name="Lecture",
                last_name=f"Seule{index}",
            ),
        )

    terminology = await seed_terminology(session)

    return LocalDevSeedReport(
        permissions_created=permissions_created,
        clinics=2,
        sites=3,
        roles=len(roles),
        users=users,
        password=LOCAL_DEV_PASSWORD,
        terminology=terminology,
    )
