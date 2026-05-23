#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../test-suite/run.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="${CHANGEFORGE_CODEGEN_CASE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-$(cd "$SCRIPT_DIR/../../../../.." && pwd)}"

python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" tests "$CASE_DIR/starter-repo"

if [[ "${CHANGEFORGE_CODEGEN_SMOKE:-0}" == "1" ]]; then
  exit 0
fi

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
if python3 -m pytest --version >/dev/null 2>&1; then
  python3 -m pytest "$SCRIPT_DIR/tests"
else
  python3 -m unittest discover -s "$SCRIPT_DIR/tests"
fi
