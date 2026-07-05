# Test Suite

## Required Checks

- Verify each branch initializes status before read.
- Verify public enum/API behavior is unchanged.
- Verify diagnostics are not suppressed as the fix.

## Fixtures

Use active, inactive, missing, and error status inputs.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Missing input must not read uninitialized status.
- Error input must return the documented status.
- Warning suppression must fail review.
