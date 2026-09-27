"""Load local development seed data into MySQL."""

from __future__ import annotations

import asyncio

from ent.core.db.session import dispose_engine, get_session_factory
from ent.seeds.dev_seed_export import write_dev_seed_output
from ent.seeds.local_dev import seed_local_dev
from ent.seeds.paths import dev_seed_output_json_path, dev_seed_output_txt_path
from ent.settings import load_settings


async def _run() -> int:
    load_settings()
    factory = get_session_factory()
    async with factory() as session:
        report = await seed_local_dev(session)
        await session.commit()

    write_dev_seed_output(report)

    print("Local dev seed complete (identity, auth, terminology, demo patients).")
    print(f"  Permissions newly created: {report.permissions_created}")
    print(f"  Clinics: {report.clinics}  Sites: {report.sites}  Roles: {report.roles}")
    print(f"  Users: {len(report.users)}")
    print(
        "  Terminology: "
        f"{report.terminology.concepts} concepts, "
        f"{report.terminology.translations} translations, "
        f"{report.terminology.value_sets} value sets",
    )
    print(f"  Demo patients created this run: {report.patients_created}")
    print("  Input:  dev-seed-data.json  (edit demo charts, then re-run seed)")
    print(f"  Output: {dev_seed_output_txt_path().name}  (email / password / role)")
    print(f"          {dev_seed_output_json_path().name}  (same logins, JSON)")
    print(f"  Password (all demo users): {report.password}")
    print("  Sample logins:")
    for user in report.users[:5]:
        print(f"    - {user.email} ({user.role_code})")
    print("    - ... more @demo.entshifa.local users in the database")
    print()
    print("  Login: POST /api/v1/auth/login")
    print(
        '  Body: {"email":"admin@demo.entshifa.local","password":"'
        + report.password
        + '"}'
    )
    await dispose_engine()
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
