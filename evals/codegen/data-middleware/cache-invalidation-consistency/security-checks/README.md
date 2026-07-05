# Security Checks

## Threat Surface

This benchmark touches cache invalidation, transaction consistency, read freshness, observability. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that cache keys include tenant and account identity.
- Verify that invalidation is ordered with transaction commit or uses a durable outbox.
- Verify that tests cover stale read, failed write, and concurrent update cases.
- Verify that metrics expose invalidation errors and stale read fallbacks.

## Rejection Cases

- Reject any solution that uses relying only on TTL expiry for correctness after writes.
- Reject any solution that uses evicting cache before a transaction can still roll back.
- Reject any solution that uses using cache keys without tenant or account scoping.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
