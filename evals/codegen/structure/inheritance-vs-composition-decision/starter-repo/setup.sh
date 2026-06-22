#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-$(cd "$SCRIPT_DIR/../../../../.." && pwd)}"
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" setup "$SCRIPT_DIR"
