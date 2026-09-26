"""Direct-import boundary check for feature routers (architecture §2)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
ROUTERS = API_ROOT / "src" / "ent" / "features"
FORBIDDEN_TAIL = frozenset({"repository", "models"})


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if any(part in FORBIDDEN_TAIL for part in parts):
                violations.append(f"{path.relative_to(API_ROOT)} imports {node.module}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if any(part in FORBIDDEN_TAIL for part in parts):
                    violations.append(
                        f"{path.relative_to(API_ROOT)} imports {alias.name}",
                    )
    return violations


def main() -> int:
    violations: list[str] = []
    for router in sorted(ROUTERS.glob("*/router.py")):
        violations.extend(_forbidden_imports(router))

    if violations:
        for line in violations:
            print(line, file=sys.stderr)
        return 1

    print("router direct-import check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
