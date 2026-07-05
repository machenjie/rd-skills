# Security Checks

## Threat Surface

This benchmark touches durable side effects, DLQ replay, operational metadata, and integration boundaries. A flawed implementation can duplicate writes, hide poison messages, or leak sensitive payloads into logs and DLQ records.

## Required Checks

- Verify that commits happen after durable side effects, not before.
- Verify that DLQ records include enough metadata for replay without logging full sensitive payloads by default.
- Verify that retry limits prevent infinite immediate retry loops.
- Verify that replay procedure preserves idempotency.

## Rejection Cases

- Reject any solution that uses enable.auto.commit=true for business-critical processing.
- Reject any solution that ack/commits before durable write.
- Reject any solution that uses infinite immediate retry.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
