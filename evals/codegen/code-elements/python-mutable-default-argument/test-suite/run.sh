#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../test-suite/run.sh
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
python3 "$ROOT_DIR/scripts/codegen_benchmark_harness.py" tests "$CASE_DIR/starter-repo"

TARGET_DIR="${CHANGEFORGE_CODEGEN_CANDIDATE_DIR:-$(pwd)}"

run_actual_tests() {
  (
    cd "$TARGET_DIR"
    PYTHONPATH="$TARGET_DIR${PYTHONPATH:+:$PYTHONPATH}" python3 -m unittest discover -s tests
  )
}

if [[ "${CHANGEFORGE_CODEGEN_SMOKE:-}" == "1" && -z "${CHANGEFORGE_CODEGEN_CANDIDATE_DIR:-}" ]]; then
  if run_actual_tests; then
    echo "expected starter implementation to fail mutable-default regression tests" >&2
    exit 1
  fi
  echo "observed expected failing starter mutable-default tests"
else
  run_actual_tests
fi
