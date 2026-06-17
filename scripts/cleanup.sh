#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -f logs/component_logs/*.jsonl logs/test_logs/*.jsonl
rm -f database/validation.db
mkdir -p logs/component_logs logs/test_logs logs/archived reports/html reports/json reports/validation_reports database

echo "Validation lab artifacts cleaned."
