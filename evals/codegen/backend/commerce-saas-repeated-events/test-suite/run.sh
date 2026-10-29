#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../test-suite/run.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="${CHANGEFORGE_CODEGEN_CASE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-}"
if [[ -z "$ROOT_DIR" ]]; then
  ROOT_DIR="$(python3 - "$SCRIPT_DIR" <<'PYROOT'
from pathlib import Path
import sys
for start in (Path.cwd().resolve(), Path(sys.argv[1]).resolve()):
    for current in (start, *start.parents):
        if (current / "scripts" / "codegen_benchmark_harness.py").is_file():
            print(current)
            raise SystemExit(0)
raise SystemExit("set CHANGEFORGE_CODEGEN_ROOT to the repository root")
PYROOT
)"
fi
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" tests "$CASE_DIR/starter-repo"
