"""Write repo-root login reference after seeding (email, password, role per user)."""

from __future__ import annotations

import json
from typing import Any

from ent.seeds.local_dev import LocalDevSeedReport
from ent.seeds.paths import (
    dev_seed_output_json_path,
    dev_seed_output_txt_path,
)


def _login_rows(report: LocalDevSeedReport) -> list[dict[str, str]]:
    password = report.password
    rows: list[dict[str, str]] = []
    for user in sorted(report.users, key=lambda u: (u.role_code, u.email)):
        rows.append(
            {
                "role": user.role_code,
                "email": user.email,
                "password": password,
            },
        )
    return rows


def write_dev_seed_output(report: LocalDevSeedReport) -> None:
    """Refresh ``dev-seed-output.json`` and ``dev-seed-output.txt`` at the repo root."""

    logins = _login_rows(report)
    payload: dict[str, Any] = {
        "users": logins,
    }

    json_path = dev_seed_output_json_path()
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines: list[str] = []
    current_role: str | None = None
    for row in logins:
        if row["role"] != current_role:
            if lines:
                lines.append("")
            lines.append(f"[{row['role']}]")
            current_role = row["role"]
        lines.append(f"{row['email']}\t{row['password']}")

    txt_path = dev_seed_output_txt_path()
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
