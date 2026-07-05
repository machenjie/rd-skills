# Test Suite

## Required Checks

- Verify suspended status behavior.
- Verify active status behavior.
- Verify unknown status behavior.
- Verify warnings are not merely silenced.

## Fixtures

Use suspended, active, unknown, and default status fixtures.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Suspended must not accidentally take active behavior.
- Intentional fallthrough must be explicit.
- Warning suppression must fail review.
