# Test Suite

## Required Checks

- Normal order event delivery reaches notification, audit, and search indexing subscribers.
- Unsubscribe removes a subscriber and cleanup runs at shutdown.
- Observer exception breaks main transaction is rejected by tests or review.
- Unbounded observers and no metrics or logs are rejected.

## Fixtures

- Order-created event fixture.
- Subscriber that throws.
- Slow subscriber that forces backpressure.
- Subscription handle fixture for unsubscribe.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- No unsubscribe must fail review.
- Unbounded observers must fail review.
- Observer exception breaks main transaction must fail tests.
- No metrics or logs must fail reliability review.
