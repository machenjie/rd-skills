#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="${CHANGEFORGE_CODEGEN_CASE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-}"
if [[ -z "$ROOT_DIR" ]]; then
  ROOT_DIR="$(SCRIPT_DIR="$SCRIPT_DIR" python3 - <<'PY'
import os
from pathlib import Path

starts = [Path(os.environ["SCRIPT_DIR"]).resolve(), Path.cwd().resolve()]
for start in starts:
    for cur in (start, *start.parents):
        if (cur / "scripts" / "codegen_benchmark_harness.py").is_file():
            print(cur)
            raise SystemExit(0)
raise SystemExit("could not locate scripts/codegen_benchmark_harness.py; set CHANGEFORGE_CODEGEN_ROOT")
PY
)"
fi
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" security "$CASE_DIR/starter-repo"

