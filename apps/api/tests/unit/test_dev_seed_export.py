from __future__ import annotations

import json
from pathlib import Path

import pytest

from ent.seeds.dev_seed_export import write_dev_seed_output
from ent.seeds.identity import SeededUser
from ent.seeds.local_dev import LocalDevSeedReport
from ent.seeds.terminology import TerminologySeedReport


@pytest.fixture
def output_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(
        "ent.seeds.dev_seed_export.dev_seed_output_json_path",
        lambda: tmp_path / "dev-seed-output.json",
    )
    monkeypatch.setattr(
        "ent.seeds.dev_seed_export.dev_seed_output_txt_path",
        lambda: tmp_path / "dev-seed-output.txt",
    )
    return tmp_path


def test_write_dev_seed_output_lists_email_password_and_role(
    output_dir: Path,
) -> None:
    report = LocalDevSeedReport(
        permissions_created=0,
        clinics=2,
        sites=3,
        roles=5,
        users=[
            SeededUser(
                email="doctor1@demo.entshifa.local",
                role_code="doctor",
                public_id="01USER",
            ),
            SeededUser(
                email="admin@demo.entshifa.local",
                role_code="clinic_admin",
                public_id="01ADMIN",
            ),
        ],
        password="LocalDevSeed1!",
        terminology=TerminologySeedReport(0, 0, 0, 0, 0),
        patients_created=0,
    )

    write_dev_seed_output(report)

    payload = json.loads(
        (output_dir / "dev-seed-output.json").read_text(encoding="utf-8")
    )
    assert payload == {
        "users": [
            {
                "role": "clinic_admin",
                "email": "admin@demo.entshifa.local",
                "password": "LocalDevSeed1!",
            },
            {
                "role": "doctor",
                "email": "doctor1@demo.entshifa.local",
                "password": "LocalDevSeed1!",
            },
        ],
    }

    txt = (output_dir / "dev-seed-output.txt").read_text(encoding="utf-8")
    assert "[clinic_admin]" in txt
    assert "admin@demo.entshifa.local\tLocalDevSeed1!" in txt
    assert "[doctor]" in txt
    assert "doctor1@demo.entshifa.local\tLocalDevSeed1!" in txt
