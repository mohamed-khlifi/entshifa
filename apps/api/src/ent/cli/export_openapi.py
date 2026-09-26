"""Export the FastAPI OpenAPI document into packages/contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ent.main import create_app
from ent.settings import load_settings

_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_OUT = _REPO_ROOT / "packages" / "contracts" / "openapi.json"


def export_openapi(out_path: Path) -> Path:
    """Build the app (schema only) and write a stable OpenAPI JSON document."""

    settings = load_settings()
    app = create_app(settings)
    # Do not start lifespan — OpenAPI is derived from route definitions only.
    document = app.openapi()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    out_path.write_text(payload, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export EntShifa OpenAPI to packages/contracts.")
    parser.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"Output path (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args(argv)
    out_path = args.out.resolve()
    written = export_openapi(out_path)
    print(f"Wrote OpenAPI to {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
