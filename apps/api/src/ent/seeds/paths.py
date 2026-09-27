"""Paths to repo-root seed files (editable input + generated copy-paste output)."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docker-compose.yml").is_file():
            return parent
    msg = "Could not locate repository root (expected docker-compose.yml)"
    raise RuntimeError(msg)


def dev_seed_input_path() -> Path:
    """Editable chart definitions consumed by ``python -m ent.cli.seed``."""

    return repo_root() / "dev-seed-data.json"


def dev_seed_output_json_path() -> Path:
    return repo_root() / "dev-seed-output.json"


def dev_seed_output_txt_path() -> Path:
    return repo_root() / "dev-seed-output.txt"
