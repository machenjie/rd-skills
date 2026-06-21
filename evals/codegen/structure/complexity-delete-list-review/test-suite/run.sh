#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../test-suite/run.sh
# expected-command: CHANGEFORGE_CODEGEN_EVALUATE=1 bash ../test-suite/run.sh
python3 ../../../../../scripts/codegen_benchmark_harness.py tests "$PWD"
if [[ "${CHANGEFORGE_CODEGEN_EVALUATE:-0}" == "1" ]]; then
  python3 ../test-suite/tests/assert_complexity_delete_list.py "$PWD"
fi
