#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash setup.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${CHANGEFORGE_CODEGEN_ROOT:-}"
if [[ -z "$ROOT_DIR" ]]; then
  ROOT_DIR="$(python3 - "$SCRIPT_DIR" <<'PYROOT'
from pathlib import Path
import sys

starts = (Path.cwd().resolve(), Path(sys.argv[1]).resolve())
seen = set()
for start in starts:
    for cur in (start, *start.parents):
        if cur in seen:
            continue
        seen.add(cur)
        if (cur / "scripts" / "codegen_benchmark_harness.py").is_file():
            print(cur)
            raise SystemExit(0)
raise SystemExit("could not locate codegen_benchmark_harness.py")
PYROOT
)"
fi
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" setup "$SCRIPT_DIR"
