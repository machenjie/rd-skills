#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../test-suite/run.sh
python3 ../../../../../scripts/codegen_benchmark_harness.py tests "$PWD"
if [[ "${CHANGEFORGE_CODEGEN_EVALUATE:-0}" == "1" ]]; then
  python3 ../test-suite/tests/assert_dependency_ladder.py "$PWD"
fi
