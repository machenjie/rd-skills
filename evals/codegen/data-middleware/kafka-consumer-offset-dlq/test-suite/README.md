# Test Suite

## Required Checks

- Manual offset commit occurs only after durable side effects.
- Duplicate message delivery is idempotent.
- Poison messages are retried a bounded number of times and sent to DLQ.
- Consumer lag and DLQ depth alerting are represented.

## Fixtures

- Fixture data for duplicate Kafka delivery.
- Fixture data for poison message retry exhaustion.
- Fixture data for offset commit ordering.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: enable.auto.commit=true for business-critical processing.
- Reject shortcut: Ack/commit before durable write.
- Reject shortcut: Infinite immediate retry.
- Existing successful behavior remains available after the new guard or compatibility path is added.
