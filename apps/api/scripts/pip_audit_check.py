"""Run pip-audit and fail only on advisories not in the allowlist."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ALLOWLIST_PATH = Path(__file__).with_name("pip_audit_allowlist.txt")


def _load_allowlist() -> set[str]:
    ids: set[str] = set()
    for raw in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        ids.add(line)
    return ids


def main() -> int:
    allow = _load_allowlist()
    result = subprocess.run(
        [sys.executable, "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"],
        capture_output=True,
        text=True,
        check=False,
    )
    # pip-audit exits 1 when vulnerabilities exist; still parse JSON from stdout.
    payload = result.stdout.strip()
    if not payload:
        print(result.stderr or "pip-audit produced no output", file=sys.stderr)
        return result.returncode or 1

    import json

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print(payload, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return 1

    # pip-audit JSON shapes vary by version; support list and dict forms.
    deps = data if isinstance(data, list) else data.get("dependencies", [])
    unexpected: list[str] = []
    for dep in deps:
        name = dep.get("name", "?")
        for vuln in dep.get("vulns", []) or []:
            vid = str(vuln.get("id") or vuln.get("aliases", ["?"])[0])
            if vid in allow:
                continue
            aliases = {str(a) for a in (vuln.get("aliases") or [])}
            if aliases & allow:
                continue
            fix = vuln.get("fix_versions") or vuln.get("fix_version") or "?"
            unexpected.append(f"{name} {vid} (fix: {fix})")

    if unexpected:
        print("Unexpected vulnerabilities:", file=sys.stderr)
        for line in unexpected:
            print(f"  {line}", file=sys.stderr)
        print(
            "Add to apps/api/scripts/pip_audit_allowlist.txt only with a tracked upgrade plan.",
            file=sys.stderr,
        )
        return 1

    print(f"pip-audit ok ({len(allow)} allowlisted advisory id(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
