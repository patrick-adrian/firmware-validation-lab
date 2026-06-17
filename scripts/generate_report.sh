#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -c "from framework.database import init_database; from framework.test_runner import run_regression; run_regression()"
