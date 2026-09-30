"""Load seed data: system, demo, or deterministic test fixtures."""

from __future__ import annotations

import argparse
import asyncio

from ent.core.db import models_registry as _models_registry  # noqa: F401
from ent.core.db.session import dispose_engine, get_session_factory
from ent.seeds.demo import seed_demo
from ent.seeds.dev_seed_export import write_dev_seed_output
from ent.seeds.paths import dev_seed_output_json_path, dev_seed_output_txt_path
from ent.seeds.system import seed_system
from ent.seeds.test_fixtures import seed_test
from ent.settings import load_settings

TARGETS = ("system", "demo", "test", "all")


async def run_seed(target: str) -> int:
    if target not in TARGETS:
        msg = f"unknown seed target: {target}"
        raise ValueError(msg)
    load_settings()
    factory = get_session_factory()
    async with factory() as session:
        if target == "system":
            system_report = await seed_system(session)
            await session.commit()
            print("System seed complete (permissions, terminology, templates).")
            print(f"  Permissions newly created: {system_report.permissions_created}")
            print(f"  Reference rows created: {system_report.reference_rows_created}")
        elif target == "test":
            test_report = await seed_test(session)
            await session.commit()
            print("Test fixture seed complete.")
            print(f"  Clinic: {test_report.clinic_slug}")
            print(f"  Other clinic: {test_report.other_clinic_slug}")
            print(f"  Admin: {test_report.admin_email}")
            print(f"  Patient MRN: {test_report.patient_mrn}")
            print(f"  Password: {test_report.password}")
        else:
            report = await seed_demo(session)
            await session.commit()
            write_dev_seed_output(report)
            print("Demo seed complete (system data, demo clinic, demo patients).")
            print(f"  Permissions newly created: {report.permissions_created}")
            print(
                f"  Clinics: {report.clinics}  Sites: {report.sites}  Roles: {report.roles}"
            )
            print(f"  Users: {len(report.users)}")
            print(
                "  Terminology: "
                f"{report.terminology.concepts} concepts, "
                f"{report.terminology.translations} translations, "
                f"{report.terminology.value_sets} value sets",
            )
            print(f"  Demo patients created this run: {report.patients_created}")
            print("  Input:  dev-seed-data.json  (edit demo charts, then re-run seed)")
            print(
                f"  Output: {dev_seed_output_txt_path().name}  (email / password / role)"
            )
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load EntShifa seed data.")
    parser.add_argument(
        "--target",
        choices=TARGETS,
        default="all",
        help="system = reference data; demo/all = system + demo clinic; test = fixtures",
    )
    args = parser.parse_args(argv)
    raise SystemExit(asyncio.run(run_seed(args.target)))


if __name__ == "__main__":
    main()
