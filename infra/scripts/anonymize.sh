#!/usr/bin/env bash
# Build an anonymized development dump (architecture §28 / P1-11).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/apps/api"
python -m ent.cli.anonymize "$@"
