#!/usr/bin/env bash
set -euo pipefail
# expected-command: bash setup.sh
python3 ../../../../../scripts/codegen_benchmark_harness.py setup "$PWD"
