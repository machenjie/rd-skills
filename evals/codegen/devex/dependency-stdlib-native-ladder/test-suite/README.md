# Test Suite

## Required Checks

Run the benchmark harness and, during candidate evaluation, the optional
dependency assertion script.

## Fixtures

Use a fixed timestamp that should produce the same UTC string on every machine.

## Expected Commands

- `bash ../test-suite/run.sh`
- `CHANGEFORGE_CODEGEN_EVALUATE=1 bash ../test-suite/run.sh` for candidate assertions.

## Regression Cases

- Formatting is stable in UTC.
- Date formatting dependency additions are rejected without dependency ladder evidence.
- Lockfile changes are rejected unless supply-chain review is included.
