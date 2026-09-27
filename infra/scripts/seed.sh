#!/usr/bin/env bash
# Load seed_system, seed_demo, or seed_test. Default target is all (system + demo).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="${1:-all}"
cd "$ROOT/apps/api"
python -m ent.cli.seed --target "$TARGET"
