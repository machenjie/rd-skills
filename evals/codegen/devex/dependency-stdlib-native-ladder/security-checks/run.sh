#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash ../security-checks/run.sh
python3 ../../../../../scripts/codegen_benchmark_harness.py security "$PWD"
