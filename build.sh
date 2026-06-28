#!/usr/bin/env bash
# Thin build wrapper for environments without make.
# Delegates to the Python build driver so flags stay in one place (framework/config.py).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m framework.build "$@"
