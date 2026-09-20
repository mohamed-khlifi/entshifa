"""EntShifa worker entrypoint.

Shares domain code with ``apps/api`` (``python -m ent.jobs.worker`` from the
API venv, or this thin launcher with ``PYTHONPATH`` pointing at ``apps/api/src``).
"""

from __future__ import annotations

import sys
from pathlib import Path

_API_SRC = Path(__file__).resolve().parents[1] / "api" / "src"
if str(_API_SRC) not in sys.path:
    sys.path.insert(0, str(_API_SRC))

from ent.jobs.worker import main

if __name__ == "__main__":
    main()
