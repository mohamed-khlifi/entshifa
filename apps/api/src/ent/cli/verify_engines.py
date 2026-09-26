"""Run clinical known-answer tests (architecture §37 gate 5)."""

from __future__ import annotations

import pytest


def main() -> None:
    raise SystemExit(
        pytest.main(
            [
                "tests/clinical",
                "-m",
                "clinical",
                "-q",
            ],
        ),
    )


if __name__ == "__main__":
    main()
