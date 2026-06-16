# Test Suite

## Required Checks

Run the benchmark harness and, during candidate evaluation, run the optional
assertion script against the implemented starter repository.

## Fixtures

The primary fixture is the public order label behavior. Test data should include
at least one active order and one archived order.

## Expected Commands

- `bash ../test-suite/run.sh`
- `CHANGEFORGE_CODEGEN_EVALUATE=1 bash ../test-suite/run.sh` for candidate assertions.

## Regression Cases

- Active order label remains unchanged.
- Archived order label includes the required archived suffix.
- Service/factory/config/shared-utils shortcuts are rejected by review or tests.
