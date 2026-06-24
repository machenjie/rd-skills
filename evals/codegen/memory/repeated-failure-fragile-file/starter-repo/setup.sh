#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-}"
if [[ -z "$ROOT_DIR" ]]; then
  ROOT_DIR="$(python3 - "$SCRIPT_DIR" <<'PYROOT'
from pathlib import Path
import sys
for start in (Path.cwd().resolve(), Path(sys.argv[1]).resolve()):
    for cur in (start, *start.parents):
        if (cur / "scripts" / "codegen_benchmark_harness.py").is_file():
            print(cur)
            raise SystemExit(0)
raise SystemExit("could not locate scripts/codegen_benchmark_harness.py; set CHANGEFORGE_CODEGEN_ROOT")
PYROOT
)"
fi
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" setup "$SCRIPT_DIR"
