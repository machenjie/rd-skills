#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../security-checks/run.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="${CHANGEFORGE_CODEGEN_CASE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-$(cd "$SCRIPT_DIR/../../../../.." && pwd)}"
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" security "$CASE_DIR/starter-repo"
