# Test Suite

## Required Checks

- Settings reads reflect successful writes within the declared freshness boundary.
- Failed writes do not evict or repopulate cache with uncommitted data.
- Concurrent updates cannot restore stale values after a newer write.
- Invalidation failures are observable and retryable.

## Fixtures

- Fixture data for cache invalidation.
- Fixture data for transaction consistency.
- Fixture data for read freshness.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Relying only on TTL expiry for correctness after writes.
- Reject shortcut: Evicting cache before a transaction can still roll back.
- Existing successful behavior remains available after the new guard or compatibility path is added.
