# Test Suite

## Required Checks

- Unit tests for pure cancellation decisions.
- Service tests for persistence, payment, cache, event, and logging coordination.
- Error-path tests for payment failure and partial side-effect recovery.

## Fixtures

Order fixtures belong under the orders test boundary and should state which cancellation state or transition they represent.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing denial reasons are preserved.
- External payment failure is reported as retryable or compensatable according to the result contract.
- Cache invalidation happens after committed state mutation.
- Event emission does not happen when the policy denies cancellation.
