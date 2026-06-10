# Test Suite

## Required Checks

- Mapper and getter database, cache, event, and external API side effects are rejected.
- Event before commit behavior is rejected unless explicit safety evidence exists.
- Cache mutation names source of truth and invalidation behavior.
- Tests cover idempotency, compensation, timeout, cancellation, retry, and cleanup for external I/O.

## Fixtures

Order side-effect fixtures belong to the order service boundary and must name input source, mutation, transaction, cache, event, and external I/O expectations.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Denied status changes do not publish events.
- Failed external API calls do not commit partial hidden side effects without compensation.
- Cache invalidation happens after source-of-truth mutation.
- Logging and metrics do not alter behavior.
