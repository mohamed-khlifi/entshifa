"""Enforce architecture §37 coverage thresholds on coverage.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINES_MIN = 100.0
SERVICES_MIN = 85.0
OVERALL_MIN = 70.0


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lower()


def main() -> int:
    report_path = Path("coverage.json")
    if not report_path.is_file():
        print("coverage.json missing; run pytest with --cov-report=json", file=sys.stderr)
        return 1

    data = json.loads(report_path.read_text(encoding="utf-8"))
    overall = float(data["totals"]["percent_covered"])
    failures: list[str] = []

    if overall < OVERALL_MIN:
        failures.append(f"overall {overall:.1f}% < {OVERALL_MIN}%")

    engine_files = [
        (path, info["summary"]["percent_covered"])
        for path, info in data["files"].items()
        if "/ent/engines/" in _normalize(path) or "\\ent\\engines\\" in path.lower()
    ]
    if engine_files:
        for path, pct in engine_files:
            if pct < ENGINES_MIN:
                failures.append(f"engines {path}: {pct:.1f}% < {ENGINES_MIN}%")
    else:
        # Package exists but has no measured lines until calculators ship.
        pass

    service_covered = 0
    service_total = 0
    for path, info in data["files"].items():
        norm = _normalize(path)
        if norm.endswith("/service.py") and "/features/" in norm:
            service_covered += int(info["summary"]["covered_lines"])
            service_total += int(info["summary"]["num_statements"])
    if service_total:
        service_pct = 100.0 * service_covered / service_total
        if service_pct < SERVICES_MIN:
            failures.append(
                f"services layer {service_pct:.1f}% < {SERVICES_MIN}% "
                f"({service_covered}/{service_total} statements)",
            )
    service_files = [
        path
        for path in data["files"]
        if _normalize(path).endswith("/service.py") and "/features/" in _normalize(path)
    ]

    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        return 1

    print(
        f"coverage thresholds ok (overall {overall:.1f}%, "
        f"{len(service_files)} service module(s))",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
