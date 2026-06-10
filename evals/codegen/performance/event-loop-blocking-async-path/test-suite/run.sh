#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../test-suite/run.sh
python3 ../../../../../scripts/codegen_benchmark_harness.py tests "$PWD"
